# Экспорт оценок из Кинопоиска

Этот шаг нужен, чтобы получить файл:

```text
ratings.csv
```

Дальше именно этот CSV используется для конвертации в IMDb и импорта в Letterboxd.

В моём случае экспорт с Кинопоиска удалось сделать через старый Node/Puppeteer-скрипт для экспорта оценок, но не “из коробки”: его пришлось немного пропатчить под текущую страницу Кинопоиска.

---

## Что должно получиться

На выходе нужен CSV с оценками.

Желательный набор колонок:

```text
dateTime,url,isSeries,name,originalName,year,duration,isWatched,userVote,rating,votes,ratingImdb,votesImdb
```

Минимально важные колонки:

```text
name
originalName
year
userVote
```

Где:

```text
name          локальное / русское название
originalName  оригинальное название
year          год фильма
userVote      ваша оценка от 1 до 10
```

Пример:

```csv
dateTime,url,isSeries,name,originalName,year,duration,isWatched,userVote,rating,votes,ratingImdb,votesImdb
2024-01-01,https://www.kinopoisk.ru/film/301/,false,Матрица,The Matrix,1999,136,true,10,8.5,1000000,8.7,2000000
```

Обезличенный пример лежит здесь:

```text
examples/kinopoisk_ratings_example.csv
```

---

## Рабочий способ, который сработал

Сначала я попробовал браузерное расширение для экспорта Кинопоиска, но оно упало с ошибкой:

```text
Can not find your user
```

После этого сработал старый Node/Puppeteer-экспортёр оценок Кинопоиска.

Запуск был примерно такой:

```bash
node kinopoisk-list-export.js https://www.kinopoisk.ru/user/<numeric_id>/votes/ ratings.csv
```

Важный момент: числовой ID профиля оказался надёжнее, чем URL с ником.

Вместо:

```text
https://www.kinopoisk.ru/user/some_nickname/votes/
```

лучше использовать:

```text
https://www.kinopoisk.ru/user/<numeric_id>/votes/
```

В моём случае именно числовой URL позволил нормально добраться до страницы оценок.

---

## Почему старый скрипт не заработал сразу

Скрипт был написан под старую разметку Кинопоиска и ждал элемент:

```js
select.navigator_per_page
```

На текущей странице этого элемента уже могло не быть.

Проблемный код выглядел примерно так:

```js
const $navigatorPerPage = await page.waitForSelector('select.navigator_per_page');
await $navigatorPerPage.press('PageDown');
await page.waitForNavigation();
```

Из-за этого экспорт падал ещё до нормальной выгрузки.

---

## Патч 1: не падать, если `navigator_per_page` нет

Проблемный участок нужно заменить на безопасный вариант:

```js
try {
  const $navigatorPerPage = await page.waitForSelector('select.navigator_per_page', { timeout: 5000 });
  await $navigatorPerPage.press('PageDown');
  await page.waitForNavigation({ timeout: 10000 }).catch(() => {});
} catch (e) {
  console.log('navigator_per_page not found, continuing...');
}
```

Смысл патча:

```text
если старый селектор есть — используем его
если селектора нет — не падаем, а продолжаем экспорт
```

---

## Патч 2: убрать лишний `waitForNavigation`

После записи заголовков CSV в старом скрипте мог быть лишний вызов:

```js
await page.waitForNavigation();
```

Если страница в этот момент никуда не переходит, скрипт просто зависает или падает по timeout.

Этот лишний `waitForNavigation()` нужно убрать или заменить на безопасный вариант:

```js
await page.waitForNavigation({ timeout: 10000 }).catch(() => {});
```

В моём случае помогло именно убрать лишнее ожидание навигации после записи headers.

---

## Что получилось после патчей

После правок экспорт прошёл успешно.

В моём случае:

```text
в профиле было примерно 1820 оценок
экспортировалось 1607 записей
```

Это не 100%, но уже достаточно, чтобы дальше восстановить профиль вкуса через IMDb и Letterboxd.

---

## Почему экспорт мог выгрузить не все оценки

Даже успешный экспорт может дать меньше записей, чем показывает профиль.

Причины могут быть такие:

```text
часть оценок относится к сериалам
часть относится к ТВ-шоу
часть страниц имеет другую разметку
экспортёр не прошёл какие-то элементы
Кинопоиск поменял интерфейс
часть записей не попала в старый список / votes
```

Для дальнейшей задачи это не критично.

Цель — не музейная точность архива, а перенос основного ядра оценок.

Если из условных 1800 оценок удалось качественно выгрузить 1300–1600, это уже рабочая база для Letterboxd.

---

## Почему полного экспортёра нет в этом репозитории

Полный `kinopoisk-list-export.js` не включён в репозиторий по двум причинам.

### 1. Это был сторонний скрипт

Если использовать чужой код, нужно учитывать лицензию и автора.

Без этого лучше не складывать полный файл в публичный репозиторий.

### 2. Экспорт Кинопоиска легко ломается

Кинопоиск может изменить:

```text
разметку страницы
пагинацию
селекторы
поведение профиля
антибот-защиту
```

Поэтому в репозитории зафиксирован не “вечный экспортёр”, а проверенный подход:

```text
старый Node/Puppeteer exporter
↓
числовой URL профиля
↓
патч navigator_per_page
↓
убрать лишний waitForNavigation
↓
получить ratings.csv
```

---

## Что проверить перед конвертацией

Перед запуском:

```bash
python scripts/kp_to_imdb.py ratings.csv
```

откройте `ratings.csv` и проверьте:

```text
есть ли колонка userVote
есть ли год фильма
есть ли originalName или name
оценки находятся в диапазоне 1–10
файл сохранён в UTF-8
```

Если Excel показывает кракозябры, открывайте CSV через импорт:

```text
Excel
→ Data
→ From Text/CSV
→ File Origin: 65001 UTF-8
→ Delimiter: comma
```

Или используйте Google Sheets.

---

## Минимальный тестовый CSV

Если хочется проверить конвертацию до запуска на полном файле, можно создать маленький `ratings.csv`:

```csv
dateTime,url,isSeries,name,originalName,year,duration,isWatched,userVote,rating,votes,ratingImdb,votesImdb
2024-01-01,https://www.kinopoisk.ru/film/301/,false,Матрица,The Matrix,1999,136,true,10,8.5,1000000,8.7,2000000
```

И запустить:

```bash
python scripts/kp_to_imdb.py ratings.csv
```

Если всё работает, появятся:

```text
imdb_import_ready.csv
matched_review.csv
unmatched.csv
```

---

## Главное

Экспорт с Кинопоиска возможен.

Но на момент этой миграции он был не кнопкой “скачать всё”, а небольшим археологическим квестом:

```text
старый экспортёр
↓
сломанный селектор
↓
патч
↓
числовой ID профиля
↓
CSV
```

После получения CSV дальше маршрут уже стабильнее:

```text
ratings.csv
↓
IMDb ID
↓
IMDb
↓
Letterboxd
```
