## Kinopoisk → IMDb → Letterboxd ratings migration
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
````

## Что здесь есть

```text
scripts/
  kp_to_imdb.py                 Конвертация CSV Кинопоиска в CSV для IMDb
  kp_to_imdb_akas.py            Дополнительный матчинг через IMDb alternative titles
  imdb_bulk_rater_console.js    Импорт оценок в IMDb через DevTools Console
  kinopoisk_votes_exporter.js   Экспорт оценок Кинопоиска в CSV через Puppeteer

docs/
  workflow.md                   Полный маршрут миграции
  troubleshooting.md            Типовые ошибки и решения
  kinopoisk_export_notes.md     Заметки по экспорту из Кинопоиска

examples/
  kinopoisk_ratings_example.csv
  imdb_import_ready_example.csv
  unmatched_example.csv
  letterboxd_ratings_example.csv
```

## Быстрый маршрут

1. Экспортировать оценки Кинопоиска в `ratings.csv`:

```bash
npm install puppeteer
node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```
2. Запустить конвертацию:

```bash
python scripts/kp_to_imdb.py ratings.csv
```

3. Получить файлы:

```text
imdb_import_ready.csv
matched_review.csv
unmatched.csv
```

4. Открыть IMDb, залогиниться и вставить в DevTools Console код из:

```text
scripts/imdb_bulk_rater_console.js
```

5. Выбрать `imdb_import_ready.csv` и дождаться импорта.
6. В IMDb сделать export оценок.
7. В Letterboxd импортировать IMDb CSV.
8. В Letterboxd искать людей через фильмы-маркеры и потом использовать `Activity from friends`.

## Требования

* Python 3.10+
* браузер с DevTools
* аккаунт IMDb
* аккаунт Letterboxd

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
```

В репозитории должны лежать только обезличенные примеры из папки `examples/`.

## Документация

Начинать лучше отсюда:

```text
docs/workflow.md
```

Если что-то ломается:

```text
docs/troubleshooting.md
```

Если непонятно, как получить CSV из Кинопоиска:

```text
docs/kinopoisk_export_notes.md
```

## Основной сценарий после миграции

После импорта оценок в Letterboxd задача не заканчивается.

Дальше нужно найти людей с похожим вкусом:

1. Выбрать фильмы-маркеры.
2. Открыть рецензии на Letterboxd.
3. Отфильтровать рецензии по своей оценке.
4. Открыть профиль автора.
5. Посмотреть общие фильмы.
6. Если вкус похож — нажать `Follow`.

После этого на страницах фильмов можно смотреть:

```text
Activity from friends
Reviews from people you follow
Watched by friends
Liked by friends
```

Это и есть практическая замена старой кинопоисковской логики: смотреть не только общий рейтинг, а оценки людей, чей вкус уже проверен.

## Ограничения

Этот репозиторий не обещает идеальную миграцию 100% оценок.

Часть фильмов может не сматчиться из-за:

```text
разных названий
ошибок в годе
сериалов и ТВ-шоу
локальных фильмов
отсутствия фильма в IMDb
```

Но для восстановления профиля вкуса обычно важнее перенести основное ядро оценок, а не абсолютно каждую запись.

License

MIT.
