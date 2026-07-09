# Kinopoisk → IMDb → Letterboxd ratings migration

Набор скриптов и пошаговая инструкция для переноса оценок из Кинопоиска в IMDb и Letterboxd.

Главная цель — не просто сохранить оценки, а восстановить рабочий сценарий:

```text
много старых оценок
↓
профиль вкуса в Letterboxd
↓
люди с похожим вкусом
↓
Activity from friends как фильтр "смотреть / не смотреть"
```

## Что здесь есть

```text
scripts/
  kp_to_imdb.py                 Конвертация CSV Кинопоиска в CSV для IMDb
  kp_to_imdb_akas.py            Дополнительный матчинг через IMDb alternative titles
  imdb_bulk_rater_console.js    Импорт оценок в IMDb через DevTools Console

docs/
  workflow.md                   Полный маршрут миграции
  github_upload_browser.md      Как залить это в GitHub через браузер
  troubleshooting.md            Типовые ошибки и решения
  kinopoisk_export_notes.md     Заметки по экспорту из Кинопоиска
  habr_article.md               Черновик статьи

examples/
  kinopoisk_ratings_example.csv
  imdb_import_ready_example.csv
  unmatched_example.csv
  letterboxd_ratings_example.csv
```

## Быстрый маршрут

1. Экспортировать оценки Кинопоиска в `ratings.csv`.
2. Запустить:

```bash
python scripts/kp_to_imdb.py ratings.csv
```

3. Получить:

```text
imdb_import_ready.csv
matched_review.csv
unmatched.csv
```

4. Открыть IMDb, залогиниться, вставить в DevTools Console код из:

```text
scripts/imdb_bulk_rater_console.js
```

5. Выбрать `imdb_import_ready.csv` и дождаться импорта.
6. В IMDb сделать export оценок.
7. В Letterboxd импортировать IMDb CSV.
8. В Letterboxd искать людей через фильмы-маркеры и потом использовать `Activity from friends`.

## Требования

- Python 3.10+
- Браузер с DevTools
- Аккаунт IMDb
- Аккаунт Letterboxd

## Важно про приватность

Не коммитьте свои реальные CSV с оценками, если не хотите публично раскрывать историю просмотров и оценок.

В `.gitignore` уже добавлены типовые файлы:

```text
ratings.csv
unmatched.csv
matched_review.csv
imdb_import_ready.csv
```

## Документация

Начинать лучше отсюда:

```text
docs/workflow.md
```

Если что-то ломается:

```text
docs/troubleshooting.md
```
