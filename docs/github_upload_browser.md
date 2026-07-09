# Как залить репозиторий на GitHub через браузер

Это вариант без `git clone`, без терминала и без привязки локального Git.

## 1. Создать репозиторий

1. Откройте GitHub в браузере.
2. В правом верхнем углу нажмите `+`.
3. Нажмите `New repository`.
4. В поле `Repository name` вставьте:

```text
kinopoisk-imdb-letterboxd-migration
```

5. В `Description` вставьте:

```text
Tools and notes for migrating Kinopoisk ratings to IMDb and Letterboxd.
```

6. Выберите `Public`.
7. Галочку `Add a README file` лучше НЕ ставить, потому что README уже есть в архиве.
8. Нажмите `Create repository`.

## 2. Загрузить файлы

1. После создания пустого репозитория нажмите `uploading an existing file`.

Если такой ссылки нет:

1. Нажмите `Add file`.
2. Нажмите `Upload files`.

## 3. Что именно загружать

Распакуйте архив `kinopoisk-imdb-letterboxd-migration-repo.zip`.

Внутри будет папка:

```text
kinopoisk-imdb-letterboxd-migration/
```

Откройте её на компьютере.

В GitHub upload перетащите НЕ zip-файл, а содержимое папки:

```text
README.md
LICENSE
.gitignore
scripts/
docs/
examples/
```

То есть в репозитории на верхнем уровне должны оказаться `README.md`, `scripts`, `docs`, `examples`, а не одна папка-матрёшка.

## 4. Commit changes

Внизу страницы будет блок `Commit changes`.

В поле commit message вставьте:

```text
Initial migration toolkit
```

Оставьте `Commit directly to the main branch`.

Нажмите:

```text
Commit changes
```

## 5. Проверка

После загрузки на главной странице репозитория должны быть:

```text
README.md
LICENSE
.gitignore
scripts/
docs/
examples/
```

Откройте `README.md`. GitHub должен красиво отрендерить инструкцию.

## 6. Как вставить ссылку в статью

В статье на Хабре можно написать:

```markdown
Все скрипты, примеры CSV и troubleshooting лежат в репозитории:
https://github.com/<ваш-ник>/kinopoisk-imdb-letterboxd-migration
```

Лучше вставить ссылку в три места:

1. После блока "что получилось".
2. Перед техническими шагами.
3. В самом конце статьи.
