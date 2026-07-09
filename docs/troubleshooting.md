# Troubleshooting

Типовые проблемы при переносе оценок:

```text
Кинопоиск → CSV
CSV → IMDb ID
IMDb import
IMDb → Letterboxd
поиск похожих людей в Letterboxd
```

---

## Kinopoisk Exporter пишет `Can not find your user`

Старые расширения и экспортёры могут не понимать новые URL профилей Кинопоиска.

Попробуйте использовать числовой ID пользователя вместо ника.

Вместо:

```text
https://www.kinopoisk.ru/user/some_nickname/votes/
```

попробуйте:

```text
https://www.kinopoisk.ru/user/<numeric_id>/votes/
```

Где `<numeric_id>` — числовой ID профиля.

---

## Экспортёр Кинопоиска падает на `select.navigator_per_page`

Некоторые старые Puppeteer-скрипты были написаны под старую разметку Кинопоиска.

Если видите ошибку вокруг:

```text
select.navigator_per_page
```

значит скрипт ждёт элемент, которого на странице уже нет.

Проблемный код может выглядеть так:

```js
const el = await page.waitForSelector('select.navigator_per_page');
await el.press('PageDown');
```

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

Смысл патча: если элемента нет, не падать, а продолжить экспорт.

---

## Экспорт Кинопоиска дал меньше оценок, чем было в профиле

Это нормальная ситуация.

Причины могут быть такие:

```text
часть оценок относится к сериалам
часть относится к ТВ-шоу
страницы отличаются по разметке
часть данных не отдаётся экспортёром
Кинопоиск поменял интерфейс
```

Для восстановления профиля вкуса не обязательно перенести 100% оценок.

Если из условных 1800 оценок удалось качественно перенести 1300–1500, этого уже достаточно для дальнейшей работы.

---

## CSV открылся в Excel кракозябрами

Файлы сохраняются в UTF-8.

Excel иногда открывает UTF-8 как ANSI, поэтому русские названия выглядят сломанными.

Открывайте через импорт:

```text
Excel
→ Data
→ From Text/CSV
→ File Origin: 65001 UTF-8
→ Delimiter: comma
```

Или используйте Google Sheets.

---

## `kp_to_imdb.py` не запускается

Проверьте, что установлен Python:

```bash
python --version
```

Нужен Python 3.10+.

Если команда `python` не работает, попробуйте:

```bash
py --version
```

Тогда запуск будет таким:

```bash
py scripts/kp_to_imdb.py ratings.csv
```

---

## `kp_to_imdb.py` пишет, что не найден `ratings.csv`

Проверьте, что файл лежит в корне проекта.

Структура должна быть примерно такой:

```text
kinopoisk-imdb-letterboxd-migration/
  ratings.csv
  scripts/
    kp_to_imdb.py
```

Запускать нужно из корня проекта:

```bash
python scripts/kp_to_imdb.py ratings.csv
```

Если файл называется иначе, передайте его имя явно:

```bash
python scripts/kp_to_imdb.py my_kinopoisk_export.csv
```

---

## `kp_to_imdb.py` нашёл меньше фильмов, чем ожидалось

Это нормально.

Скрипт матчить фильмы по названию и году. Он специально не делает слишком агрессивный матчинг, чтобы не перепутать фильмы.

Частые причины unmatched:

```text
другое английское название
ошибка или отличие в годе
сериал вместо фильма
ТВ-шоу
короткометражка
локальный фильм
фильма нет в IMDb
```

Можно попробовать разрешить расхождение по году:

```bash
python scripts/kp_to_imdb.py ratings.csv --year-window 1
```

Но осторожно: чем шире окно по году, тем выше риск ложных совпадений.

После такого запуска обязательно проверьте `matched_review.csv` глазами.

---

## В `matched_review.csv` есть неправильные совпадения

Такое возможно.

Что делать:

1. Откройте `matched_review.csv`.
2. Найдите неправильную строку.
3. Удалите соответствующий IMDb ID из `imdb_import_ready.csv`.
4. При желании найдите правильный IMDb ID вручную и добавьте строку руками.

Формат строки:

```csv
const,your rating
tt0133093,10
```

Где:

```text
const        IMDb ID
your rating  ваша оценка от 1 до 10
```

---

## `_csv.Error: field larger than field limit`

В скриптах уже добавлен увеличенный лимит:

```python
csv.field_size_limit(2147483647)
```

Если на вашей системе это всё равно падает, замените значение в скрипте на меньшее:

```python
csv.field_size_limit(100000000)
```

---

## `kp_to_imdb_akas.py` работает слишком долго

Это ожидаемо.

`kp_to_imdb_akas.py` читает IMDb dataset:

```text
title.akas.tsv.gz
```

Это большой файл с альтернативными названиями.

Этот шаг необязательный.

Практический совет:

```text
если kp_to_imdb.py уже перенёс большую часть оценок,
kp_to_imdb_akas.py можно пропустить
```

В моём случае AKAs дали небольшой прирост, но заняли много времени.

---

## IMDb import через старые userscript'ы не работает

Многие старые userscript'ы для IMDb больше не находятся или не работают.

В этом репозитории используется другой путь:

```text
scripts/imdb_bulk_rater_console.js
```

Сценарий:

```text
открыть IMDb
залогиниться
открыть DevTools Console
вставить JS
выбрать imdb_import_ready.csv
дождаться завершения
```

---

## IMDb import через Console ничего не делает

Проверьте:

```text
вы открыли именно imdb.com
вы залогинены
вы вставили весь JS-код целиком
браузер не заблокировал file picker
CSV содержит правильные колонки
```

Ожидаемый формат CSV:

```csv
const,your rating
tt0133093,10
tt0111161,9
```

---

## IMDb import выдаёт ошибки по части фильмов

Сначала попробуйте увеличить задержку в файле:

```text
scripts/imdb_bulk_rater_console.js
```

Найдите строку:

```js
const DELAY_MS = 500;
```

Поменяйте на:

```js
const DELAY_MS = 1000;
```

Если ошибок немного, можно импортировать остальное и потом вручную разобраться с failed rows.

После завершения failed rows доступны в консоли как:

```js
window.imdbBulkRatingFailed
```

---

## IMDb import прошёл, но оценки не сразу видны

Подождите немного и обновите страницу IMDb.

Иногда интерфейс обновляется не мгновенно.

Проверьте страницу:

```text
Your Ratings
```

---

## Letterboxd import не принимает CSV

Убедитесь, что вы загружаете именно CSV, экспортированный из IMDb, а не `imdb_import_ready.csv`.

Правильная цепочка такая:

```text
imdb_import_ready.csv
↓
импорт в IMDb через Console
↓
IMDb Your Ratings → Export
↓
этот IMDb CSV импортируется в Letterboxd
```

`imdb_import_ready.csv` нужен для IMDb, не для Letterboxd.

---

## Оценки в Letterboxd выглядят “в два раза меньше”

Это нормально.

IMDb использует шкалу 1–10.

Letterboxd использует шкалу 0.5–5.

Соответствие:

```text
IMDb 10 → Letterboxd 5★
IMDb 9  → Letterboxd 4.5★
IMDb 8  → Letterboxd 4★
IMDb 7  → Letterboxd 3.5★
IMDb 6  → Letterboxd 3★
IMDb 5  → Letterboxd 2.5★
IMDb 4  → Letterboxd 2★
IMDb 3  → Letterboxd 1.5★
IMDb 2  → Letterboxd 1★
IMDb 1  → Letterboxd 0.5★
```

---

## Внешние Letterboxd compare-сервисы ничего не показывают

Это бывает.

Причины:

```text
большой профиль
ограничения сервиса
таймауты
неполное чтение данных
изменения на стороне Letterboxd
```

Не стоит строить весь процесс только на compare-сервисах.

Рабочий ручной способ:

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

---

## Как понять, что пользователь Letterboxd “мой”

Не по одному фильму.

Один общий фильм с одинаковой оценкой ничего не доказывает.

Проверяйте:

```text
совпадают ли любимые фильмы
совпадают ли нелюбимые фильмы
нет ли большого количества жёстких расхождений
много ли у человека оценок
активен ли профиль
```

Хороший кандидат:

```text
1000+ оценок
много общих фильмов
похожие оценки по спорным фильмам
живой профиль
```

Плохой кандидат:

```text
мало оценок
совпадение только по одному фильму
сильные расхождения по вашим маркерам
профиль давно неактивен
```

---

## Я подписался на похожих людей. Что дальше?

Теперь не нужно ходить по каждому профилю.

Открывайте страницу фильма и смотрите:

```text
Activity from friends
Reviews from people you follow
Watched by friends
Liked by friends
```

Именно это становится практической заменой старого сценария Кинопоиска.

---

## Не хочу светить свои оценки

Не публикуйте реальные CSV.

В публичный репозиторий кладите только обезличенные примеры:

```text
examples/
  kinopoisk_ratings_example.csv
  imdb_import_ready_example.csv
  unmatched_example.csv
  letterboxd_ratings_example.csv
```

Файлы с реальными оценками уже добавлены в `.gitignore`.

---

## Что можно спокойно удалить после миграции

После успешного переноса можно удалить локально:

```text
title.basics.tsv.gz
title.akas.tsv.gz
matched_review.csv
matched_review_akas.csv
unmatched.csv
still_unmatched.csv
imdb_import_ready.csv
imdb_import_ready_akas.csv
```

Но лучше оставить резервную копию исходного `ratings.csv` где-нибудь у себя локально.

Не коммитьте его в публичный репозиторий.
