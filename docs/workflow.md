# Workflow: Кинопоиск → IMDb → Letterboxd

Полный маршрут:

```text
Кинопоиск → ratings.csv → IMDb ID → IMDb → Letterboxd → люди с похожим вкусом
```

## 0. Что понадобится

```text
Node.js 18+
Python 3.10+
установленный Google Chrome или Microsoft Edge
аккаунт IMDb
аккаунт Letterboxd
профиль Кинопоиска с оценками
```

## 1. Экспортировать оценки из Кинопоиска

```bash
npm install
node scripts/kinopoisk_votes_exporter.js "https://www.kinopoisk.ru/user/<numeric_id>/votes/" ratings.csv
```

Экспортёр явно обходит бакеты оценок 1/10 … 10/10:

```text
/votes/list/vote/1/vs/vote/
...
/votes/list/vote/10/vs/vote/
```

Это защищает от ухода в разделы актёров/персон по случайным ссылкам пагинации.

Если Кинопоиск покажет логин/капчу/security check:

```text
1. пройти проверку руками в открытом браузере
2. вернуться в терминал
3. нажать Enter
```

На выходе должен появиться `ratings.csv`.

Минимально важные колонки:

```text
name
originalName
year
userVote
```

## 2. Конвертировать в IMDb format

```bash
python scripts/kp_to_imdb.py ratings.csv
```

На Windows, если `python` не работает:

```bash
py scripts/kp_to_imdb.py ratings.csv
```

На выходе:

```text
imdb_import_ready.csv
matched_review.csv
unmatched.csv
```

## 3. Проверить матчинг

Откройте `matched_review.csv` и проверьте несколько строк глазами: год, название, ремейки, сериалы.

`unmatched.csv` — это фильмы, которые не удалось найти автоматически. Это нормально.

## 4. Необязательный AKAs-матчинг

```bash
python scripts/kp_to_imdb_akas.py unmatched.csv
```

Шаг тяжёлый, потому что читает большой IMDb dataset `title.akas.tsv.gz`.

## 5. Импорт в IMDb

1. Открыть IMDb.
2. Залогиниться.
3. Открыть DevTools → Console.
4. Вставить код из `scripts/imdb_bulk_rater_console.js`.
5. Выбрать `imdb_import_ready.csv`.
6. Дождаться завершения.

Если делали AKAs-матчинг, повторить для `imdb_import_ready_akas.csv`.

## 6. IMDb → Letterboxd

1. IMDb → `Your Ratings` → `Export`.
2. Letterboxd → `Settings` → `Import & Export`.
3. Импортировать IMDb CSV.

Соответствие шкал:

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

## 7. Найти людей с похожим вкусом

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

Хорошие маркеры:

```text
спорный фильм, который вы любите
фильм, который многие хвалят, а вы не любите
фильм, где ваша оценка сильно отличается от средней
```

После подписки на 5–10 подходящих людей открывайте страницу фильма и смотрите:

```text
Activity from friends
Reviews from people you follow
Watched by friends
Liked by friends
```

## 8. Что делать с новыми оценками

Практический вариант:

```text
Letterboxd = основной сервис для новых оценок
IMDb = архив / резервная база
```

## 9. Если что-то сломалось

Смотрите:

```text
docs/troubleshooting.md
```
