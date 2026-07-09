#!/usr/bin/env python3
"""
Second-pass matching through IMDb alternative titles.

Input:
    unmatched.csv from kp_to_imdb.py

Output:
    imdb_import_ready_akas.csv
    matched_review_akas.csv
    still_unmatched.csv

Usage:
    python scripts/kp_to_imdb_akas.py unmatched.csv
    python scripts/kp_to_imdb_akas.py unmatched.csv --year-window 1

Warning:
    This script reads IMDb title.akas.tsv.gz. The file is large.
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
from typing import Dict, List, Optional, Set

IMDB_BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
IMDB_AKAS_URL = "https://datasets.imdbws.com/title.akas.tsv.gz"

DEFAULT_TYPES = {"movie", "tvMovie", "tvSeries", "tvMiniSeries", "tvSpecial", "video", "short"}
TYPE_PRIORITY = {"movie": 0, "tvMovie": 1, "tvSeries": 2, "tvMiniSeries": 3, "tvSpecial": 4, "video": 5, "short": 6}

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


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def build_targets(rows: List[dict]) -> Dict[str, List[int]]:
    targets: Dict[str, List[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        if parse_int(row.get("year") or row.get("Year")) is None:
            continue
        for title in candidate_titles(row):
            key = normalize_title(title)
            if key:
                targets[key].append(idx)
    return targets


def collect_aka_candidates(akas_path: Path, targets: Dict[str, List[int]]) -> Dict[str, List[dict]]:
    candidate_by_title_id: Dict[str, List[dict]] = defaultdict(list)
    print(f"Reading IMDb AKAs: {akas_path}")
    with open_maybe_gzip(akas_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for i, row in enumerate(reader, 1):
            if i % 2_000_000 == 0:
                print(f"  processed {i:,} AKA rows, candidate titleIds: {len(candidate_by_title_id):,}")
            aka_title = row.get("title", "")
            key = normalize_title(aka_title)
            if key not in targets:
                continue
            title_id = row.get("titleId", "")
            if not title_id:
                continue
            for source_idx in targets[key]:
                candidate_by_title_id[title_id].append({
                    "sourceIndex": source_idx,
                    "akaTitle": aka_title,
                    "akaRegion": row.get("region", ""),
                    "akaLanguage": row.get("language", ""),
                    "akaTypes": row.get("types", ""),
                    "akaAttributes": row.get("attributes", ""),
                })
    print(f"AKA candidate titleIds: {len(candidate_by_title_id):,}")
    return candidate_by_title_id


def validate_candidates_with_basics(basics_path: Path, rows: List[dict], candidate_by_title_id: Dict[str, List[dict]], allowed_types: Set[str], year_window: int, skip_adult: bool = True) -> Dict[int, List[dict]]:
    valid_by_source_idx: Dict[int, List[dict]] = defaultdict(list)
    print(f"Validating candidates with IMDb basics: {basics_path}")
    with open_maybe_gzip(basics_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for i, row in enumerate(reader, 1):
            if i % 1_000_000 == 0:
                print(f"  processed {i:,} IMDb rows")
            title_id = row.get("tconst", "")
            if title_id not in candidate_by_title_id:
                continue
            title_type = row.get("titleType", "")
            if title_type not in allowed_types:
                continue
            if skip_adult and row.get("isAdult") == "1":
                continue
            imdb_year = parse_int(row.get("startYear"))
            if imdb_year is None:
                continue
            for candidate in candidate_by_title_id[title_id]:
                source_idx = candidate["sourceIndex"]
                source_year = parse_int(rows[source_idx].get("year") or rows[source_idx].get("Year"))
                if source_year is None:
                    continue
                year_diff = abs(imdb_year - source_year)
                if year_diff > year_window:
                    continue
                valid = dict(candidate)
                valid.update({
                    "imdbId": title_id,
                    "imdbTitle": row.get("primaryTitle", ""),
                    "imdbOriginalTitle": row.get("originalTitle", ""),
                    "imdbYear": imdb_year,
                    "imdbType": title_type,
                    "matchReason": "AKA exact year" if year_diff == 0 else f"AKA year ±{year_diff}",
                    "yearDiff": year_diff,
                })
                valid_by_source_idx[source_idx].append(valid)
    return valid_by_source_idx


def pick_best(candidates: List[dict]) -> dict:
    candidates = list(candidates)
    candidates.sort(key=lambda item: (item.get("yearDiff", 99), TYPE_PRIORITY.get(item.get("imdbType", ""), 99), item.get("imdbId", "")))
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", help="unmatched.csv from kp_to_imdb.py")
    parser.add_argument("--out-dir", default=".", help="Output directory")
    parser.add_argument("--basics", default="title.basics.tsv.gz", help="Path to IMDb title.basics.tsv.gz")
    parser.add_argument("--akas", default="title.akas.tsv.gz", help="Path to IMDb title.akas.tsv.gz")
    parser.add_argument("--year-window", type=int, default=0, help="Allow matching by year ±N")
    parser.add_argument("--types", default=",".join(sorted(DEFAULT_TYPES)), help="Comma-separated IMDb title types to include")
    parser.add_argument("--include-adult", action="store_true", help="Do not skip IMDb adult titles")
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    out_dir = Path(args.out_dir)
    basics_path = Path(args.basics)
    akas_path = Path(args.akas)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_csv.exists():
        print(f"Input file not found: {input_csv}", file=sys.stderr)
        return 1

    download_if_missing(basics_path, IMDB_BASICS_URL)
    download_if_missing(akas_path, IMDB_AKAS_URL)

    rows = read_csv_rows(input_csv)
    targets = build_targets(rows)
    if not targets:
        print("No target titles found in input CSV", file=sys.stderr)
        return 1

    candidate_by_title_id = collect_aka_candidates(akas_path, targets)
    allowed_types = {x.strip() for x in args.types.split(",") if x.strip()}
    valid_by_source_idx = validate_candidates_with_basics(basics_path, rows, candidate_by_title_id, allowed_types, args.year_window, skip_adult=not args.include_adult)

    matched_rows, still_unmatched_rows, import_rows = [], [], []
    for idx, row in enumerate(rows):
        rating = parse_rating(row.get("userVote") or row.get("your rating") or row.get("rating"))
        candidates = valid_by_source_idx.get(idx, [])
        if rating is None:
            row = dict(row)
            row["unmatchedReasonAkas"] = "missing or invalid userVote"
            still_unmatched_rows.append(row)
            continue
        if not candidates:
            row = dict(row)
            row["unmatchedReasonAkas"] = "no AKA title/year match"
            still_unmatched_rows.append(row)
            continue
        best = pick_best(candidates)
        merged = dict(row)
        merged.update(best)
        merged["your rating"] = rating
        matched_rows.append(merged)
        import_rows.append({"const": best["imdbId"], "your rating": rating})

    original_fields = list(rows[0].keys()) if rows else []
    matched_fields = original_fields + ["imdbId", "imdbTitle", "imdbOriginalTitle", "imdbYear", "imdbType", "akaTitle", "akaRegion", "akaLanguage", "akaTypes", "akaAttributes", "matchReason", "your rating"]
    unmatched_fields = original_fields + ["unmatchedReasonAkas"]

    write_csv(out_dir / "imdb_import_ready_akas.csv", import_rows, ["const", "your rating"])
    write_csv(out_dir / "matched_review_akas.csv", matched_rows, matched_fields)
    write_csv(out_dir / "still_unmatched.csv", still_unmatched_rows, unmatched_fields)

    print(f"\nInput rows:       {len(rows)}")
    print(f"Matched with AKA: {len(matched_rows)}")
    print(f"Still unmatched:  {len(still_unmatched_rows)}")
    print(f"\nWritten: {out_dir / 'imdb_import_ready_akas.csv'}")
    print(f"Written: {out_dir / 'matched_review_akas.csv'}")
    print(f"Written: {out_dir / 'still_unmatched.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
