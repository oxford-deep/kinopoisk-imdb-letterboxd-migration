#!/usr/bin/env python3
"""
Convert Kinopoisk ratings CSV to IMDb ratings import CSV.

Input:
    ratings.csv exported from Kinopoisk or another tool.

Expected useful columns:
    name, originalName, year, userVote

Output:
    imdb_import_ready.csv
    matched_review.csv
    unmatched.csv

Usage:
    python scripts/kp_to_imdb.py ratings.csv
    python scripts/kp_to_imdb.py ratings.csv --year-window 1
"""

from __future__ import annotations

import argparse
import csv
import gzip
import re
import sys
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IMDB_BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"

DEFAULT_TYPES = {
    "movie", "tvMovie", "tvSeries", "tvMiniSeries", "tvSpecial", "video", "short",
}

TYPE_PRIORITY = {
    "movie": 0, "tvMovie": 1, "tvSeries": 2, "tvMiniSeries": 3,
    "tvSpecial": 4, "video": 5, "short": 6,
}

try:
    csv.field_size_limit(2147483647)
except OverflowError:
    csv.field_size_limit(100000000)


def normalize_title(value: str) -> str:
    if value is None:
        return ""
    value = unicodedata.normalize("NFKC", str(value)).strip().lower()
    value = value.replace("ё", "е").replace("&", " and ")
    value = re.sub(r"\s*\([^)]*\)\s*", " ", value)
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    for article in ("the ", "a ", "an "):
        if value.startswith(article):
            value = value[len(article):].strip()
    return value


def parse_int(value: object) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text == r"\N":
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_rating(value: object) -> Optional[int]:
    rating = parse_int(value)
    if rating is None:
        return None
    return rating if 1 <= rating <= 10 else None


def download_if_missing(path: Path, url: str) -> None:
    if path.exists():
        return
    print(f"Downloading {url}")
    print(f"Saving to {path}")
    with urllib.request.urlopen(url) as response, path.open("wb") as out:
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            total += len(chunk)
            if total and total % (50 * 1024 * 1024) < 1024 * 1024:
                print(f"  downloaded ~{total // (1024 * 1024)} MB")


def open_maybe_gzip(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("r", encoding="utf-8", newline="")


def read_csv_rows(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        return list(csv.DictReader(f, dialect=dialect))


def build_imdb_index(basics_path: Path, allowed_types: set[str], skip_adult: bool = True) -> Dict[Tuple[str, int], List[dict]]:
    index: Dict[Tuple[str, int], List[dict]] = defaultdict(list)
    print(f"Reading IMDb basics: {basics_path}")
    with open_maybe_gzip(basics_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for i, row in enumerate(reader, 1):
            if i % 1_000_000 == 0:
                print(f"  processed {i:,} IMDb rows")
            title_type = row.get("titleType", "")
            if title_type not in allowed_types:
                continue
            if skip_adult and row.get("isAdult") == "1":
                continue
            year = parse_int(row.get("startYear"))
            if year is None:
                continue
            title_id = row.get("tconst", "")
            primary = row.get("primaryTitle", "")
            original = row.get("originalTitle", "")
            keys = {normalize_title(primary), normalize_title(original)}
            keys.discard("")
            for key in keys:
                index[(key, year)].append({
                    "imdbId": title_id,
                    "imdbTitle": primary,
                    "imdbOriginalTitle": original,
                    "imdbYear": year,
                    "imdbType": title_type,
                })
    print(f"Index keys: {len(index):,}")
    return index


def candidate_titles(row: dict) -> List[str]:
    values = [row.get("originalName"), row.get("name"), row.get("title"), row.get("Title")]
    seen, result = set(), []
    for value in values:
        if value is None:
            continue
        value = str(value).strip()
        if not value:
            continue
        key = normalize_title(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def find_match(row: dict, index: Dict[Tuple[str, int], List[dict]], year_window: int) -> Tuple[Optional[dict], str]:
    year = parse_int(row.get("year") or row.get("Year"))
    if year is None:
        return None, "missing year"
    titles = candidate_titles(row)
    if not titles:
        return None, "missing title"
    normalized_titles = [normalize_title(t) for t in titles]
    normalized_titles = [t for t in normalized_titles if t]
    candidates = []
    for normalized in normalized_titles:
        for diff in range(0, year_window + 1):
            years = [year] if diff == 0 else [year - diff, year + diff]
            for y in years:
                for cand in index.get((normalized, y), []):
                    candidates.append((diff, normalized, cand))
    if not candidates:
        return None, "no title/year match"
    candidates.sort(key=lambda item: (item[0], TYPE_PRIORITY.get(item[2]["imdbType"], 99), item[2]["imdbId"]))
    diff, normalized, cand = candidates[0]
    cand = dict(cand)
    cand["matchTitle"] = normalized
    cand["matchReason"] = "exact year" if diff == 0 else f"year ±{diff}"
    return cand, "matched"


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", help="Kinopoisk ratings CSV")
    parser.add_argument("--out-dir", default=".", help="Output directory")
    parser.add_argument("--basics", default="title.basics.tsv.gz", help="Path to IMDb title.basics.tsv.gz")
    parser.add_argument("--year-window", type=int, default=0, help="Allow matching by year ±N")
    parser.add_argument("--types", default=",".join(sorted(DEFAULT_TYPES)), help="Comma-separated IMDb title types to include")
    parser.add_argument("--include-adult", action="store_true", help="Do not skip IMDb adult titles")
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    out_dir = Path(args.out_dir)
    basics_path = Path(args.basics)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_csv.exists():
        print(f"Input file not found: {input_csv}", file=sys.stderr)
        return 1

    download_if_missing(basics_path, IMDB_BASICS_URL)
    allowed_types = {x.strip() for x in args.types.split(",") if x.strip()}
    index = build_imdb_index(basics_path, allowed_types, skip_adult=not args.include_adult)
    rows = read_csv_rows(input_csv)

    matched_rows, unmatched_rows, import_rows = [], [], []
    for row in rows:
        rating = parse_rating(row.get("userVote") or row.get("your rating") or row.get("rating"))
        if rating is None:
            row = dict(row)
            row["unmatchedReason"] = "missing or invalid userVote"
            unmatched_rows.append(row)
            continue
        match, reason = find_match(row, index, args.year_window)
        if match is None:
            row = dict(row)
            row["unmatchedReason"] = reason
            unmatched_rows.append(row)
            continue
        merged = dict(row)
        merged.update(match)
        merged["your rating"] = rating
        matched_rows.append(merged)
        import_rows.append({"const": match["imdbId"], "your rating": rating})

    original_fields = list(rows[0].keys()) if rows else []
    matched_fields = original_fields + ["imdbId", "imdbTitle", "imdbOriginalTitle", "imdbYear", "imdbType", "matchTitle", "matchReason", "your rating"]
    unmatched_fields = original_fields + ["unmatchedReason"]

    write_csv(out_dir / "imdb_import_ready.csv", import_rows, ["const", "your rating"])
    write_csv(out_dir / "matched_review.csv", matched_rows, matched_fields)
    write_csv(out_dir / "unmatched.csv", unmatched_rows, unmatched_fields)

    print(f"\nInput rows: {len(rows)}")
    print(f"Matched:    {len(matched_rows)}")
    print(f"Unmatched:  {len(unmatched_rows)}")
    print(f"\nWritten: {out_dir / 'imdb_import_ready.csv'}")
    print(f"Written: {out_dir / 'matched_review.csv'}")
    print(f"Written: {out_dir / 'unmatched.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
