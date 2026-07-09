#!/usr/bin/env node
/*
Kinopoisk votes exporter.

Usage:
  npm install
  node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv

This version uses puppeteer-core and an installed Chrome/Edge.
It does not require Puppeteer to download bundled Chrome.
*/

const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");

const [, , inputUrl, outputFile = "ratings.csv"] = process.argv;

if (!inputUrl) {
  console.error('Usage: node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<id>/votes/" ratings.csv');
  process.exit(1);
}

const NAVIGATION_TIMEOUT_MS = 60000;
const PAGE_WAIT_MS = 1500;

const CSV_HEADERS = [
  "dateTime",
  "url",
  "isSeries",
  "name",
  "originalName",
  "year",
  "duration",
  "isWatched",
  "userVote",
  "rating",
  "votes",
  "ratingImdb",
  "votesImdb",
];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function csvEscape(value) {
  if (value === null || value === undefined) return "";

  const text = String(value);
  if (/[",\r\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }

  return text;
}

function writeCsv(rows, filePath) {
  const lines = [];
  lines.push(CSV_HEADERS.join(","));

  for (const row of rows) {
    lines.push(CSV_HEADERS.map((header) => csvEscape(row[header])).join(","));
  }

  fs.writeFileSync(filePath, "\uFEFF" + lines.join("\n"), "utf8");
}

function findInstalledBrowser() {
  const candidates = [];

  if (process.platform === "win32") {
    const local = process.env.LOCALAPPDATA || "";
    const programFiles = process.env.PROGRAMFILES || "C:\\Program Files";
    const programFilesX86 = process.env["PROGRAMFILES(X86)"] || "C:\\Program Files (x86)";

    candidates.push(
      path.join(programFiles, "Google", "Chrome", "Application", "chrome.exe"),
      path.join(programFilesX86, "Google", "Chrome", "Application", "chrome.exe"),
      path.join(local, "Google", "Chrome", "Application", "chrome.exe"),
      path.join(programFiles, "Microsoft", "Edge", "Application", "msedge.exe"),
      path.join(programFilesX86, "Microsoft", "Edge", "Application", "msedge.exe"),
      path.join(local, "Microsoft", "Edge", "Application", "msedge.exe")
    );
  } else if (process.platform === "darwin") {
    candidates.push(
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
      "/Applications/Chromium.app/Contents/MacOS/Chromium"
    );
  } else {
    candidates.push(
      "/usr/bin/google-chrome",
      "/usr/bin/google-chrome-stable",
      "/usr/bin/chromium",
      "/usr/bin/chromium-browser",
      "/usr/bin/microsoft-edge",
      "/usr/bin/microsoft-edge-stable"
    );
  }

  for (const candidate of candidates) {
    if (candidate && fs.existsSync(candidate)) {
      return candidate;
    }
  }

  return null;
}

function votesPageUrl(baseUrl, pageNumber) {
  const url = new URL(baseUrl);

  let pathname = url.pathname;
  pathname = pathname.replace(/\/page\/\d+\/?/, "/");
  pathname = pathname.replace(/\/+$/, "/");

  if (pageNumber > 1) {
    pathname += `page/${pageNumber}/`;
  }

  url.pathname = pathname;
  return url.href;
}

async function waitForHumanIfNeeded(page) {
  const title = await page.title().catch(() => "");
  const bodyText = await page.evaluate(() => document.body ? document.body.innerText.slice(0, 2000) : "").catch(() => "");

  const looksLikeCaptcha =
    /captcha|капча|security|проверка|робот|robot|access denied|доступ/i.test(title) ||
    /captcha|капча|security check|проверка|робот|robot|access denied|доступ ограничен/i.test(bodyText);

  if (!looksLikeCaptcha) return;

  console.log("");
  console.log("Kinopoisk seems to show captcha / security / login page.");
  console.log("Solve it manually in the opened browser, then press Enter here.");
  console.log("");

  await new Promise((resolve) => {
    process.stdin.resume();
    process.stdin.once("data", () => resolve());
  });
}

async function trySetMaxPerPage(page) {
  try {
    const select = await page.waitForSelector("select.navigator_per_page", { timeout: 5000 });
    await select.press("PageDown");
    await page.waitForNavigation({ timeout: 10000 }).catch(() => {});
    console.log("navigator_per_page found and changed.");
  } catch {
    console.log("navigator_per_page not found, continuing...");
  }
}

async function extractRowsFromPage(page) {
  return await page.evaluate(() => {
    function text(el) {
      return el ? (el.textContent || "").replace(/\s+/g, " ").trim() : "";
    }

    function attr(el, name) {
      return el ? (el.getAttribute(name) || "") : "";
    }

    function absUrl(url) {
      if (!url) return "";

      try {
        return new URL(url, location.origin).href;
      } catch {
        return url;
      }
    }

    function first(root, selectors) {
      for (const selector of selectors) {
        const el = root.querySelector(selector);
        if (el) return el;
      }
      return null;
    }

    function allFilmLinks() {
      return Array
        .from(document.querySelectorAll('a[href*="/film/"], a[href*="/series/"]'))
        .filter((a) => /\/(film|series)\/\d+\/?/.test(a.getAttribute("href") || ""));
    }

    function closestItem(link) {
      const selectors = [".item", ".profileFilmsList__item", ".styles_root__", "li", "tr", "article"];

      for (const selector of selectors) {
        const node = link.closest(selector);
        if (node && text(node).length > text(link).length) return node;
      }

      return link.parentElement || link;
    }

    function parseYear(raw) {
      const match = String(raw || "").match(/\b(18|19|20)\d{2}\b/);
      return match ? match[0] : "";
    }

    function parseDuration(raw) {
      const match = String(raw || "").match(/(\d{1,3})\s*(мин|m|min)/i);
      return match ? match[1] : "";
    }

    function parseFloatText(raw) {
      const match = String(raw || "").replace(",", ".").match(/\b\d{1,2}(?:\.\d)?\b/);
      return match ? match[0] : "";
    }

    function parseUserVote(itemText, item) {
      const voteEl = first(item, [
        ".vote",
        ".userVote",
        ".rating__value",
        "[class*='userVote']",
        "[class*='vote']",
        "[class*='rating']",
      ]);

      const fromElement = parseFloatText(text(voteEl));
      if (fromElement) return fromElement;

      const match = itemText.match(/(?:моя оценка|ваша оценка|оценка)\D{0,20}([1-9]|10)\b/i);
      return match ? match[1] : "";
    }

    function parseOriginalName(item, itemText, localName) {
      const originalEl = first(item, [".nameEng", ".name-original", "[class*='original']", "[class*='secondary']"]);

      const direct = text(originalEl);
      if (direct) {
        return direct
          .replace(/\b(18|19|20)\d{2}\b/g, "")
          .replace(/\d{1,3}\s*(мин|m|min)/ig, "")
          .replace(/\s+/g, " ")
          .trim();
      }

      const lines = itemText
        .split(/\n| {2,}/)
        .map((x) => x.trim())
        .filter(Boolean);

      const localIndex = lines.findIndex((line) => line === localName);
      if (localIndex >= 0 && lines[localIndex + 1]) {
        const candidate = lines[localIndex + 1]
          .replace(/\b(18|19|20)\d{2}\b/g, "")
          .replace(/\d{1,3}\s*(мин|m|min)/ig, "")
          .replace(/\s+/g, " ")
          .trim();

        if (candidate && candidate !== localName) return candidate;
      }

      return "";
    }

    function parseRatings(itemText) {
      const kpMatch = itemText.match(/КиноПоиск\D{0,20}(\d+(?:[.,]\d+)?)/i);
      const imdbMatch = itemText.match(/IMDb\D{0,20}(\d+(?:[.,]\d+)?)/i);

      return {
        rating: kpMatch ? kpMatch[1].replace(",", ".") : "",
        votes: "",
        ratingImdb: imdbMatch ? imdbMatch[1].replace(",", ".") : "",
        votesImdb: "",
      };
    }

    const seen = new Set();
    const rows = [];

    for (const link of allFilmLinks()) {
      const href = absUrl(attr(link, "href"));
      const idMatch = href.match(/\/(film|series)\/(\d+)\/?/);
      if (!idMatch) continue;

      const uniqueKey = `${idMatch[1]}:${idMatch[2]}`;
      if (seen.has(uniqueKey)) continue;
      seen.add(uniqueKey);

      const item = closestItem(link);
      const itemText = text(item);
      const localName = text(link);

      if (!localName) continue;

      const originalName = parseOriginalName(item, itemText, localName);
      const year = parseYear(itemText);
      const duration = parseDuration(itemText);
      const userVote = parseUserVote(itemText, item);
      const ratings = parseRatings(itemText);

      rows.push({
        dateTime: "",
        url: href,
        isSeries: idMatch[1] === "series" ? "true" : "false",
        name: localName,
        originalName,
        year,
        duration,
        isWatched: "true",
        userVote,
        rating: ratings.rating,
        votes: ratings.votes,
        ratingImdb: ratings.ratingImdb,
        votesImdb: ratings.votesImdb,
      });
    }

    return rows;
  });
}

async function hasNextPage(page, currentPage) {
  return await page.evaluate((currentPage) => {
    const links = Array.from(document.querySelectorAll("a[href]"));
    const nextText = links.some((a) => /след|next|›|»/i.test(a.textContent || ""));
    const nextNumber = links.some((a) => (a.textContent || "").trim() === String(currentPage + 1));
    return nextText || nextNumber;
  }, currentPage);
}

async function launchBrowser() {
  const executablePath = findInstalledBrowser();

  if (!executablePath) {
    throw new Error("Could not find installed Chrome/Edge. Install Google Chrome or Microsoft Edge, then run the script again.");
  }

  console.log(`Using browser: ${executablePath}`);

  return await puppeteer.launch({
    executablePath,
    headless: false,
    defaultViewport: null,
    args: ["--start-maximized", "--disable-blink-features=AutomationControlled"],
  });
}

(async () => {
  const outputPath = path.resolve(outputFile);
  const browser = await launchBrowser();

  const page = await browser.newPage();
  page.setDefaultNavigationTimeout(NAVIGATION_TIMEOUT_MS);
  page.setDefaultTimeout(NAVIGATION_TIMEOUT_MS);

  await page.setUserAgent(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  );

  const allRows = [];
  const seenUrls = new Set();

  try {
    console.log(`Opening: ${inputUrl}`);
    await page.goto(inputUrl, { waitUntil: "domcontentloaded" });
    await waitForHumanIfNeeded(page);
    await trySetMaxPerPage(page);

    let pageNumber = 1;
    let emptyPages = 0;

    while (pageNumber <= 500) {
      const url = votesPageUrl(inputUrl, pageNumber);

      console.log("");
      console.log(`Page ${pageNumber}: ${url}`);

      await page.goto(url, { waitUntil: "domcontentloaded" }).catch(async (error) => {
        console.warn(`Navigation warning: ${error.message}`);
      });

      await waitForHumanIfNeeded(page);
      await sleep(PAGE_WAIT_MS);

      const rows = await extractRowsFromPage(page);
      const newRows = [];

      for (const row of rows) {
        const key = row.url || `${row.name}-${row.year}-${row.userVote}`;
        if (!seenUrls.has(key)) {
          seenUrls.add(key);
          newRows.push(row);
          allRows.push(row);
        }
      }

      console.log(`Found on page: ${rows.length}. New: ${newRows.length}. Total: ${allRows.length}.`);

      if (newRows.length === 0) {
        emptyPages += 1;
      } else {
        emptyPages = 0;
      }

      writeCsv(allRows, outputPath);
      console.log(`Saved: ${outputPath}`);

      const nextExists = await hasNextPage(page, pageNumber);

      if (!nextExists && pageNumber > 1) {
        console.log("No next page detected. Stopping.");
        break;
      }

      if (emptyPages >= 2) {
        console.log("Two empty pages in a row. Stopping.");
        break;
      }

      pageNumber += 1;
    }

    console.log("");
    console.log(`Done. Exported rows: ${allRows.length}`);
    console.log(`CSV: ${outputPath}`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
