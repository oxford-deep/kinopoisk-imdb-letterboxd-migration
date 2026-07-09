# Troubleshooting

Типовые проблемы при переносе оценок:

```text
Кинопоиск → ratings.csv
ratings.csv → IMDb ID
IMDb import
IMDb → Letterboxd
поиск похожих людей в Letterboxd
```

---

## `npm` не найден

Для экспортёра Кинопоиска нужен Node.js.

Проверьте:

```bash
node --version
npm --version
```

Если команды не работают, установите Node.js:

```text
https://nodejs.org/
```

После установки откройте новый терминал и проверьте версии ещё раз.

---

## `npm install puppeteer` долго работает или скачивает браузер

Это нормально.

Puppeteer обычно скачивает совместимый Chromium/Chrome. Это может занять время.

Команда:

```bash
npm install puppeteer
```

Если установка завершилась без ошибок, можно запускать экспорт:

```bash
node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```

---

## `node` пишет, что не может найти `kinopoisk_votes_exporter.js`

Проверьте, что запускаете команду из корня проекта.

Структура должна быть такой:

```text
kinopoisk-imdb-letterboxd-migration/
  scripts/
    kinopoisk_votes_exporter.js
    kp_to_imdb.py
    kp_to_imdb_akas.py
    imdb_bulk_rater_console.js
```

Правильный запуск из корня:

```bash
node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```

---

## Kinopoisk Exporter / старое расширение пишет `Can not find your user`

Старые расширения могут не понимать новые URL профилей Кинопоиска.

Используйте экспортёр из этого репозитория:

```bash
node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```

И лучше используйте числовой ID профиля.

Вместо:

```text
https://www.kinopoisk.ru/user/some_nickname/votes/
```

используйте:

```text
https://www.kinopoisk.ru/user/<numeric_id>/votes/
```

---

## Как найти числовой ID профиля Кинопоиска

Откройте профиль Кинопоиска в браузере.

Если URL уже выглядит так:

```text
https://www.kinopoisk.ru/user/123456/
```

значит `123456` — это нужный ID.

Страница оценок будет:

```text
https://www.kinopoisk.ru/user/123456/votes/
```

Если у вас URL с ником, попробуйте открыть профиль, раздел оценок или старую ссылку профиля — часто Кинопоиск сам редиректит на числовой ID.

---

## Скрипт открыл браузер и просит пройти проверку

Это нормально.

Кинопоиск может показать:

```text
логин
капчу
security check
проверку, что вы не робот
```

Что делать:

```text
1. пройти проверку руками в открытом браузере
2. вернуться в терминал
3. нажать Enter
```

После этого скрипт продолжит экспорт.

---

## Скрипт пишет `navigator_per_page not found, continuing...`

Это не ошибка.

Старые страницы Кинопоиска могли иметь элемент:

```js
select.navigator_per_page
```

На текущей странице его может не быть.

В экспортёре этот кейс уже обработан:

```text
navigator_per_page not found, continuing...
```

означает:

```text
элемент не найден
скрипт не упал
экспорт продолжается
```

---

## Экспортёр нашёл 0 фильмов

Проверьте по порядку:

```text
вы открываете именно /votes/
профиль / оценки доступны в браузере
вы залогинены, если оценки закрыты
Кинопоиск не показывает капчу или заглушку
URL указан с числовым ID
```

Правильный формат:

```bash
node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```

Также откройте этот URL руками в браузере и убедитесь, что там реально виден список оценок.

---

## Экспортёр сохранил `ratings.csv`, но оценок меньше, чем в профиле

Это возможная ситуация.

Причины:

```text
часть оценок относится к сериалам
часть относится к ТВ-шоу
часть страниц имеет другую разметку
Кинопоиск поменял интерфейс
часть данных не попала в votes list
экспортёр не смог разобрать часть карточек
```

Для дальнейшей задачи это не всегда критично.

Если из условных 1800 оценок удалось качественно выгрузить 1300–1600, это уже рабочая база для переноса профиля вкуса в Letterboxd.

---

## В `ratings.csv` пустая колонка `userVote`

Это плохо: без вашей оценки строка не сможет импортироваться в IMDb.

Что проверить:

```text
на странице Кинопоиска действительно видна ваша оценка
вы открыли именно страницу своих votes
вы залогинены
Кинопоиск не показывает публичную страницу без пользовательских оценок
```

Если оценки на странице видны, но `userVote` пустой, значит Кинопоиск поменял разметку блока оценки. В этом случае нужно обновлять селекторы внутри:

```text
scripts/kinopoisk_votes_exporter.js
```

Функция, которую стоит смотреть:

```js
parseUserVote()
```

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

Структура должна быть такой:

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

```text
1. открыть matched_review.csv
2. найти неправильную строку
3. удалить соответствующий IMDb ID из imdb_import_ready.csv
4. при желании найти правильный IMDb ID вручную и добавить строку руками
```

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

Правильная цепочка:

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
