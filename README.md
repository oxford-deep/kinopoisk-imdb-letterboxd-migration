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
  kinopoisk_votes_exporter.js   Экспорт оценок Кинопоиска в CSV через Puppeteer
  kp_to_imdb.py                 Конвертация CSV Кинопоиска в CSV для IMDb
  kp_to_imdb_akas.py            Дополнительный матчинг через IMDb alternative titles
  imdb_bulk_rater_console.js    Импорт оценок в IMDb через DevTools Console

docs/
  workflow.md                   Полный маршрут миграции
  troubleshooting.md            Типовые ошибки и решения
  kinopoisk_export_notes.md     Подробности экспорта из Кинопоиска

examples/
  kinopoisk_ratings_example.csv
  imdb_import_ready_example.csv
  unmatched_example.csv
  letterboxd_ratings_example.csv
```

## Быстрый маршрут

### 1. Экспортировать оценки Кинопоиска

```bash
npm install
node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```

Экспортёр использует `puppeteer-core` и установленный Google Chrome / Microsoft Edge. Отдельный Chromium не скачивается.

### 2. Сконвертировать оценки в IMDb format

```bash
python scripts/kp_to_imdb.py ratings.csv
```

На Windows, если `python` не работает:

```bash
py scripts/kp_to_imdb.py ratings.csv
```

На выходе появятся:

```text
imdb_import_ready.csv
matched_review.csv
unmatched.csv
```

### 3. Необязательно: добить часть unmatched через IMDb AKAs

```bash
python scripts/kp_to_imdb_akas.py unmatched.csv
```

Этот шаг тяжёлый и необязательный.

### 4. Импортировать оценки в IMDb

1. Открыть IMDb.
2. Залогиниться.
3. Открыть DevTools → Console.
4. Вставить код из `scripts/imdb_bulk_rater_console.js`.
5. Выбрать `imdb_import_ready.csv`.
6. Дождаться завершения.

Если использовали AKAs-матчинг, повторить импорт для `imdb_import_ready_akas.csv`.

### 5. Перенести IMDb → Letterboxd

1. В IMDb открыть `Your Ratings`.
2. Нажать `Export`.
3. Скачать IMDb CSV.
4. В Letterboxd открыть `Settings → Import & Export`.
5. Импортировать IMDb CSV.

### 6. Найти людей с похожим вкусом

```text
фильмы-маркеры
↓
рецензии с такой же оценкой
↓
профили авторов
↓
общие фильмы
↓
Follow
↓
Activity from friends
```

После этого на страницах фильмов можно смотреть:

```text
Activity from friends
Reviews from people you follow
Watched by friends
Liked by friends
```

## Требования

```text
Node.js 18+
Python 3.10+
установленный Google Chrome или Microsoft Edge
браузер с DevTools
аккаунт IMDb
аккаунт Letterboxd
```

## Важно про приватность

Не коммитьте свои реальные CSV с оценками, если не хотите публично раскрывать историю просмотров и оценок.

В `.gitignore` уже добавлены типовые файлы:

```text
ratings.csv
unmatched.csv
still_unmatched.csv
matched_review.csv
matched_review_akas.csv
imdb_import_ready.csv
imdb_import_ready_akas.csv
title.basics.tsv.gz
title.akas.tsv.gz
```

## Документация

```text
docs/workflow.md
docs/troubleshooting.md
docs/kinopoisk_export_notes.md
```

## Ограничения

Репозиторий не обещает идеальную миграцию 100% оценок. Для восстановления профиля вкуса важнее перенести основное ядро оценок, а не абсолютно каждую запись.

## License

MIT.
