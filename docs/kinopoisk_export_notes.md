# Экспорт оценок из Кинопоиска

Этот репозиторий начинается с момента, когда у вас уже есть CSV с оценками Кинопоиска.

То есть основной маршрут такой:

```text
получить ratings.csv из Кинопоиска
↓
сконвертировать его в IMDb ID
↓
импортировать оценки в IMDb
↓
перенести их в Letterboxd
```

Универсального стабильного экспортёра Кинопоиска здесь нет.

Причина простая: Кинопоиск меняет интерфейс, разметку страниц и поведение профилей. Из-за этого старые расширения и Puppeteer-скрипты могут ломаться.

---

## Какой CSV нужен

Скрипт `kp_to_imdb.py` ожидает CSV с оценками.

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

## Что сработало в моём случае

В моём случае старое браузерное расширение не сработало.

Ошибка была примерно такая:

```text
Can not find your user
```

После этого рабочим оказался старый Node/Puppeteer-скрипт для экспорта оценок, но его пришлось патчить под текущую страницу Кинопоиска.

Запуск был примерно такой:

```bash
node kinopoisk-list-export.js https://www.kinopoisk.ru/user/<numeric_id>/votes/ ratings.csv
```

Важный момент: числовой ID пользователя оказался надёжнее, чем URL с ником.

Вместо:

```text
https://www.kinopoisk.ru/user/some_nickname/votes/
```

лучше пробовать:

```text
https://www.kinopoisk.ru/user/<numeric_id>/votes/
```

---

## Частая проблема старых Puppeteer-экспортёров

Некоторые старые скрипты ждут на странице элемент:

```js
select.navigator_per_page
```

Но в текущей разметке Кинопоиска его может не быть.

Проблемный код может выглядеть так:

```js
const $navigatorPerPage = await page.waitForSelector('select.navigator_per_page');
await $navigatorPerPage.press('PageDown');
await page.waitForNavigation();
```

Безопасный вариант:

```js
try {
  const $navigatorPerPage = await page.waitForSelector('select.navigator_per_page', { timeout: 5000 });
  await $navigatorPerPage.press('PageDown');
  await page.waitForNavigation({ timeout: 10000 }).catch(() => {});
} catch (e) {
  console.log('navigator_per_page not found, continuing...');
}
```

Смысл патча: если элемента нет, не падать, а продолжать экспорт.

---

## Почему полного экспортёра Кинопоиска нет в репозитории

Есть три причины.

### 1. Это был бы отдельный проект

Экспорт из Кинопоиска — это отдельная задача:

```text
логин
cookies
профиль
пагинация
изменения разметки
антибот
сериалы / фильмы / шоу
```

Этот репозиторий решает другую часть:

```text
CSV с оценками
↓
IMDb
↓
Letterboxd
```

### 2. Старые экспортёры могут быть чужим кодом

Если использовать чужой Puppeteer-скрипт, нужно сохранять ссылку на автора и лицензию.

Поэтому в репозитории лучше не тащить чужой код без уверенности, что его можно распространять.

### 3. Кинопоиск может снова поменять страницу

Даже если положить рабочий экспортёр сегодня, завтра он может сломаться.

Поэтому здесь зафиксирован более устойчивый контракт:

```text
на вход нужен ratings.csv с названием, годом и вашей оценкой
```

---

## Что делать, если экспортёр дал меньше оценок, чем есть в профиле

Это нормальная ситуация.

Причины могут быть такие:

```text
часть оценок относится к сериалам
часть относится к ТВ-шоу
часть страниц имеет другую разметку
экспортёр не прошёл все страницы
Кинопоиск поменял интерфейс
```

Для дальнейшей работы не обязательно вытащить 100% оценок.

Если у вас было около 1800 оценок и удалось качественно выгрузить 1300–1500, этого уже достаточно, чтобы восстановить профиль вкуса в Letterboxd.

---

## Что проверить перед запуском конвертации

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

---

## Минимальный тестовый CSV

Если хочется проверить скрипт до запуска на своём полном файле, можно создать маленький `ratings.csv`:

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

Не пытайтесь сначала идеально победить экспорт Кинопоиска.

Практический порядок такой:

```text
получили достаточно полный CSV
↓
перенесли основное ядро оценок
↓
импортировали в IMDb
↓
перенесли в Letterboxd
↓
нашли людей с похожим вкусом
```

Цель — не музейная точность архива, а рабочий профиль вкуса.
