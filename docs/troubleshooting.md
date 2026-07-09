# Troubleshooting

## `npm` не найден

Нужен Node.js 18+.

```bash
node --version
npm --version
```

## `npm install` прошёл, но раньше была ошибка `Could not find Chrome`

В старой версии использовался `puppeteer`, и npm мог заблокировать скачивание Chrome.

В актуальной версии используется:

```text
puppeteer-core
```

и установленный Google Chrome / Microsoft Edge.

Проверьте `package.json`:

```json
"puppeteer-core": "^24.43.1"
```

Если локально уже была старая установка:

```cmd
rmdir /s /q node_modules
del package-lock.json
npm install
```

## Скрипт пишет `Could not find installed Chrome/Edge`

Установите Google Chrome или Microsoft Edge.

На Windows скрипт ищет стандартные пути:

```text
C:\Program Files\Google\Chrome\Application\chrome.exe
C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
C:\Program Files\Microsoft\Edge\Application\msedge.exe
C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
```

## `node` не может найти `kinopoisk_votes_exporter.js`

Запускайте из корня проекта:

```bash
node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```

На Windows:

```cmd
node scripts\kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```

## Старое расширение пишет `Can not find your user`

Используйте экспортёр из этого репозитория и числовой ID профиля:

```text
https://www.kinopoisk.ru/user/<numeric_id>/votes/
```

## Скрипт открыл браузер и просит пройти проверку

Кинопоиск может показать логин, капчу или security check.

```text
1. пройти проверку руками в открытом браузере
2. вернуться в терминал
3. нажать Enter
```

## `navigator_per_page not found, continuing...`

Это не ошибка. Старый селектор отсутствует, экспорт продолжается.

## Скрипт уходит в `/actor/`, `/persons/` или собирает странные страницы

Это проблема старой версии, которая шла по произвольной next-ссылке.

Актуальная версия явно обходит:

```text
/votes/list/vote/1/vs/vote/
...
/votes/list/vote/10/vs/vote/
```

Замените `scripts/kinopoisk_votes_exporter.js` на актуальную версию.

## Экспортёр нашёл 0 фильмов

Проверьте:

```text
вы открываете именно /votes/
профиль / оценки доступны в браузере
вы залогинены, если оценки закрыты
Кинопоиск не показывает капчу или заглушку
URL указан с числовым ID
```

## В `ratings.csv` пустая колонка `userVote`

Актуальная версия должна заполнять `userVote` из текущего vote bucket.

Если колонка пустая, проверьте, что используете свежий `scripts/kinopoisk_votes_exporter.js`.

## CSV открылся в Excel кракозябрами

Открывайте через импорт:

```text
Excel → Data → From Text/CSV → File Origin: 65001 UTF-8 → Delimiter: comma
```

## `kp_to_imdb.py` не запускается

```bash
python --version
```

Если `python` не работает:

```bash
py scripts/kp_to_imdb.py ratings.csv
```

## `kp_to_imdb.py` пишет, что не найден `ratings.csv`

Файл должен лежать в корне проекта:

```text
kinopoisk-imdb-letterboxd-migration/
  ratings.csv
  scripts/
    kp_to_imdb.py
```

Запуск:

```bash
python scripts/kp_to_imdb.py ratings.csv
```

## `kp_to_imdb.py` нашёл меньше фильмов, чем ожидалось

Частые причины:

```text
другое английское название
ошибка или отличие в годе
сериал вместо фильма
ТВ-шоу
локальный фильм
фильма нет в IMDb
```

Можно попробовать:

```bash
python scripts/kp_to_imdb.py ratings.csv --year-window 1
```

Но после этого обязательно проверьте `matched_review.csv` глазами.

## `kp_to_imdb_akas.py` работает слишком долго

Это ожидаемо. Шаг необязательный.

## IMDb import через Console ничего не делает

Проверьте:

```text
вы открыли imdb.com
вы залогинены
вставили весь JS-код целиком
CSV содержит const,your rating
```

## Letterboxd import не принимает CSV

В Letterboxd нужно загружать CSV, экспортированный из IMDb, а не `imdb_import_ready.csv`.

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

## Внешние Letterboxd compare-сервисы ничего не показывают

Не строить весь процесс только на compare-сервисах.

Рабочий способ:

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

## Что можно удалить после миграции локально

```text
node_modules/
package-lock.json
ratings.csv
title.basics.tsv.gz
title.akas.tsv.gz
matched_review.csv
matched_review_akas.csv
unmatched.csv
still_unmatched.csv
imdb_import_ready.csv
imdb_import_ready_akas.csv
```

Резервную копию исходного `ratings.csv` лучше оставить у себя локально.
