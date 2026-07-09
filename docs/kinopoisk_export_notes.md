# Экспорт оценок из Кинопоиска

В этом репозитории нет отдельного универсального экспортёра Кинопоиска.

Причина простая: Кинопоиск меняет разметку, старые расширения и Puppeteer-скрипты могут ломаться.

## Что нужно получить

Нужен CSV с вашими оценками.

Минимальные поля:

```text
name
originalName
year
userVote
```

Желательный формат:

```text
dateTime,url,isSeries,name,originalName,year,duration,isWatched,userVote,rating,votes,ratingImdb,votesImdb
```

Пример лежит здесь:

```text
examples/kinopoisk_ratings_example.csv
```

## Что сработало в моём случае

Рабочим оказался старый Node/Puppeteer-экспортёр списков Кинопоиска, но его пришлось патчить под текущую страницу.

Проблемное место:

```js
const $navigatorPerPage = await page.waitForSelector('select.navigator_per_page');
await $navigatorPerPage.press('PageDown');
```

Патч:

```js
try {
  const $navigatorPerPage = await page.waitForSelector('select.navigator_per_page', { timeout: 5000 });
  await $navigatorPerPage.press('PageDown');
  await page.waitForNavigation({ timeout: 10000 }).catch(() => {});
} catch (e) {
  console.log('navigator_per_page not found, continuing...');
}
```

Если используете чужой экспортёр, сохраните ссылку на автора и лицензию.

## Почему в репозитории нет полного Puppeteer-экспортёра

Чтобы не тащить чужой код без лицензии и не обещать поддержку того, что может сломаться при следующем изменении Кинопоиска.

Этот репозиторий начинается с точки, где у вас уже есть `ratings.csv`.
