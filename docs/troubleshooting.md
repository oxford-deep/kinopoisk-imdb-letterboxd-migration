# Troubleshooting

## Kinopoisk Exporter пишет `Can not find your user`

Попробуйте использовать числовой ID профиля вместо ника.

Например, вместо:

```text
https://www.kinopoisk.ru/user/some_nickname/votes/
```

используйте:

```text
https://www.kinopoisk.ru/user/<numeric_id>/votes/
```

## Скрипт ждёт `select.navigator_per_page` и падает

Некоторые старые экспортёры Кинопоиска были написаны под старую разметку.

Если видите ошибку ожидания селектора:

```text
select.navigator_per_page
```

нужно либо обновить экспортёр, либо пропустить этот шаг.

Безопасный патч:

```js
try {
  const el = await page.waitForSelector('select.navigator_per_page', { timeout: 5000 });
  await el.press('PageDown');
  await page.waitForNavigation({ timeout: 10000 }).catch(() => {});
} catch (e) {
  console.log('navigator_per_page not found, continuing...');
}
```

## Python падает с `_csv.Error: field larger than field limit`

В скриптах уже есть увеличение лимита:

```python
csv.field_size_limit(2147483647)
```

Если на вашей системе это всё равно падает, замените на меньшее значение:

```python
csv.field_size_limit(100000000)
```

## Excel показывает кракозябры в CSV

Файлы сохраняются в UTF-8.

В Excel лучше открывать так:

```text
Data
→ From Text/CSV
→ File Origin: 65001 UTF-8
→ Delimiter: comma
```

Или открыть файл через Google Sheets.

## `kp_to_imdb.py` нашёл меньше фильмов, чем ожидалось

Это нормально.

Причины:

```text
разные названия
сериалы и ТВ-шоу
локальные фильмы
ошибки в годе
фильмы отсутствуют в IMDb
```

Можно попробовать:

```bash
python scripts/kp_to_imdb.py ratings.csv --year-window 1
```

Но аккуратно: чем шире окно по году, тем выше риск ложных совпадений.

## `kp_to_imdb_akas.py` работает очень долго

Это ожидаемо.

`title.akas.tsv.gz` — большой IMDb dataset. Скрипт читает его потоково, но всё равно это может занять много времени.

Если первый скрипт уже перенёс большую часть оценок, этот шаг можно пропустить.

## IMDb import через Console ничего не делает

Проверьте:

1. Вы залогинены в IMDb.
2. Вы открыли именно страницу IMDb.
3. В CSV есть колонки:

```text
const
your rating
```

4. Значения `const` выглядят так:

```text
tt0133093
```

5. Оценки находятся в диапазоне 1–10.

## IMDb import выдаёт ошибки

Попробуйте увеличить задержку в `scripts/imdb_bulk_rater_console.js`:

```js
const DELAY_MS = 700;
```

или даже:

```js
const DELAY_MS = 1200;
```

## Letterboxd compare-сервисы не находят совпадения

Это нормальная ситуация.

На больших профилях внешние compare-сервисы могут не справляться.

Практический способ:

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

## Не хочу светить личные оценки

Не публикуйте реальные CSV.

В репозитории должны лежать только обезличенные примеры из папки `examples/`.
