/*
IMDb bulk rating importer.

How to use:
1. Open imdb.com in your browser.
2. Log in.
3. Open DevTools → Console.
4. Paste this entire script and press Enter.
5. Pick imdb_import_ready.csv.
6. Wait.

Expected CSV format:
const,your rating
tt0133093,10
tt0111161,9
*/

(async () => {
  const DELAY_MS = 500;
  const GRAPHQL_URL = "https://api.graphql.imdb.com/";

  const MUTATION = `
    mutation UpdateTitleRating($rating: Int!, $titleId: ID!) {
      rateTitle(input: {rating: $rating, titleId: $titleId}) {
        rating {
          value
        }
      }
    }
  `;

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function parseCsv(text) {
    const rows = [];
    let row = [];
    let cell = "";
    let insideQuotes = false;

    for (let i = 0; i < text.length; i++) {
      const char = text[i];
      const next = text[i + 1];

      if (char === '"' && insideQuotes && next === '"') {
        cell += '"';
        i++;
        continue;
      }
      if (char === '"') {
        insideQuotes = !insideQuotes;
        continue;
      }
      if (char === "," && !insideQuotes) {
        row.push(cell);
        cell = "";
        continue;
      }
      if ((char === "\n" || char === "\r") && !insideQuotes) {
        if (char === "\r" && next === "\n") i++;
        row.push(cell);
        cell = "";
        if (row.some((value) => value.trim() !== "")) rows.push(row);
        row = [];
        continue;
      }
      cell += char;
    }

    row.push(cell);
    if (row.some((value) => value.trim() !== "")) rows.push(row);
    if (rows.length === 0) return [];

    const headers = rows[0].map((value) => value.trim().replace(/^\uFEFF/, ""));
    return rows.slice(1).map((values) => {
      const obj = {};
      headers.forEach((header, index) => {
        obj[header] = (values[index] || "").trim();
      });
      return obj;
    });
  }

  function chooseFile() {
    return new Promise((resolve, reject) => {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".csv,text/csv";
      input.style.position = "fixed";
      input.style.left = "-9999px";

      input.addEventListener("change", () => {
        const file = input.files && input.files[0];
        input.remove();
        if (!file) reject(new Error("No file selected"));
        else resolve(file);
      });

      document.body.appendChild(input);
      input.click();
    });
  }

  function normalizeRows(rows) {
    return rows
      .map((row) => {
        const titleId = row.const || row.imdbId || row.tconst || row.titleId;
        const ratingRaw = row["your rating"] || row.userVote || row.rating;
        const rating = Number.parseInt(ratingRaw, 10);
        return { titleId: String(titleId || "").trim(), rating };
      })
      .filter((row) => /^tt\d+$/.test(row.titleId) && row.rating >= 1 && row.rating <= 10);
  }

  async function rateTitle(titleId, rating) {
    const response = await fetch(GRAPHQL_URL, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/graphql+json, application/json",
      },
      body: JSON.stringify({
        operationName: "UpdateTitleRating",
        query: MUTATION,
        variables: { titleId, rating },
      }),
    });

    const text = await response.text();
    let json;
    try {
      json = JSON.parse(text);
    } catch (error) {
      throw new Error(`IMDb returned non-JSON response. HTTP ${response.status}: ${text.slice(0, 300)}`);
    }

    if (!response.ok || json.errors) {
      throw new Error(`HTTP ${response.status}: ${JSON.stringify(json.errors || json).slice(0, 500)}`);
    }

    return json;
  }

  console.log("IMDb bulk rating importer started.");
  console.log("Select CSV file with columns: const,your rating");

  const file = await chooseFile();
  const text = await file.text();
  const parsedRows = parseCsv(text);
  const rows = normalizeRows(parsedRows);

  console.log(`CSV rows: ${parsedRows.length}`);
  console.log(`Valid IMDb rating rows: ${rows.length}`);

  if (rows.length === 0) {
    console.warn("No valid rows found. Expected: const,your rating");
    return;
  }

  const failed = [];
  let successful = 0;

  for (let i = 0; i < rows.length; i++) {
    const { titleId, rating } = rows[i];
    try {
      await rateTitle(titleId, rating);
      successful++;
      if (successful % 25 === 0 || i === rows.length - 1) {
        console.log(`Progress: ${i + 1}/${rows.length}. Successful: ${successful}. Failed: ${failed.length}.`);
      }
    } catch (error) {
      failed.push({ titleId, rating, error: error.message });
      console.error(`Failed: ${titleId} → ${rating}`, error);
    }
    await sleep(DELAY_MS);
  }

  console.log("Done.");
  console.log(`Successful: ${successful}`);
  console.log(`Failed: ${failed.length}`);

  if (failed.length > 0) {
    console.table(failed);
    window.imdbBulkRatingFailed = failed;
    console.warn("Failed rows are available as window.imdbBulkRatingFailed");
  }
})();
