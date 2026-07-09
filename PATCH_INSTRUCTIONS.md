# Patch instructions

Add this file to the repository:

```text
scripts/kinopoisk_votes_exporter.js
```

Replace this file with the updated version:

```text
docs/kinopoisk_export_notes.md
```

Then update README.md and docs/workflow.md manually by adding references to the exporter.

## README.md: add to scripts list

Add this line:

```text
  kinopoisk_votes_exporter.js    Экспорт оценок Кинопоиска в CSV через Puppeteer
```

## README.md: update fast route

Replace:

```text
1. Экспортировать оценки Кинопоиска в ratings.csv.
```

with:

```text
1. Экспортировать оценки Кинопоиска в ratings.csv:
   npm install puppeteer
   node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```

## docs/workflow.md: update step 1

In step 1, add:

```bash
npm install puppeteer
node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```
