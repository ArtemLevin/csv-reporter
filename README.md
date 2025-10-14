### `README.md`

````markdown
# CSV Rating Reporter (average-rating)

> Назначение: краткая документация по установке, запуску, архитектурным решениям и вкладу в проект.  
> Данный файл **не содержит исполняемого кода** — только инструкции и пояснения.

## Кратко
CLI-утилита для локальной консолидации CSV-файлов и построения отчёта среднего рейтинга по брендам.  
Только stdlib + `tabulate`. Без сетевых вызовов и внешних сервисов.

---

## Запуск через `Make`

> Рекомендуемый способ — цели Makefile используют Python из venv и выполняют установку/тесты/запуск.

```bash
# 1) Создать виртуальное окружение и установить проект с dev-зависимостями (editable)
make install

# 2) Прогнать тесты (pytest) — цель зависит от install
make test

# 3) Запустить CLI без установки в системный PATH
#    Обязательно передайте FILES="path1.csv path2.csv"
make run FILES="products_1.csv products_2.csv" SORT=avg_rating LIMIT=10 TABLEFMT=github REPORT=average-rating

# 4) Проверка покрытия
make cov

# 5) Быстрая локальная проверка качества (format + lint + type + test)
make check

# 6) Сборка wheel/sdist
make build

# 7) Уборка артефактов и кэшей
make clean
````

Переменные, которые можно переопределять при `make run`:

* `FILES` — список CSV (`"path1.csv path2.csv"`), **обязателен**;
* `REPORT` — имя отчёта (по умолчанию `average-rating`);
* `SORT` — поле сортировки (`brand|avg_rating|items`);
* `LIMIT` — ограничение строк (целое число, неотрицательное);
* `TABLEFMT` — формат `tabulate` (`github|simple|plain|grid|fancy_grid|psql|tsv`).

---

## Быстрый старт (без Make)

Подготовьте CSV с заголовками: `name,brand,price,rating` (регистр не важен).

`products_1.csv`

```csv
name,brand,price,rating
iPhone 15,Apple,999,4.8
Pixel 9,Google,799,4.5
Galaxy S24,Samsung,899,4.6
```

`products_2.csv`

```csv
name,brand,price,rating
MacBook Air,Apple,1299,4.7
ThinkPad X1,Lenovo,1499,4.4
Some device,Unknown,199,
```

Установка вручную:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Запуск:

```bash
csvreporter --files products_1.csv products_2.csv --report average-rating
```

Пример вывода:

```
| brand   |   avg_rating |   items |
|---------|--------------|---------|
| apple   |         4.75 |       2 |
| samsung |         4.60 |       1 |
| google  |         4.50 |       1 |
| lenovo  |         4.40 |       1 |
```

---

## Архитектура (обзор)

* **CLI**: `src/csv_reporter/cli.py` — аргументы, связывание слоёв, коды выхода.
* **Data**: `csv_reader.py` — валидация заголовков, чтение CSV (UTF-8 → fallback CP1251), нормализация.
* **Domain**: `model.py` (DTO), `aggregator.py` (средние по брендам).
* **Reports**: `reports/base.py` (абстракция), `reports/average_rating.py` (реализация), `reports/registry.py` (реестр).
* **Presentation**: `presenter.py` — таблица через `tabulate` (сохранение двух знаков после запятой).
* **Infra**: `errors.py` (исключения), `logging_utils.py` (stderr-логи, таймер).

## Коды выхода и ошибки

* `0` — успех; `1` — ошибка (аргументы, схема CSV, данные, доступ к файлам).
* Сообщения ошибок — на `stderr` в формате: `Error: <описание>`.

---

## Разработка

```bash
# Локально без Make
ruff format .
ruff check .
mypy src
pytest --cov=csv_reporter --cov-report=term-missing
```

---

## Расширение отчётов

Добавление `average-price`:

1. Создайте `reports/average_price.py` c классом `AveragePriceReport(Report)`.
2. Зарегистрируйте в `get_default_registry()` или вызовите `register` в клиентском коде.
3. Запускайте: `--report average-price`.

---

## Ограничения

* До ~10k строк (≈2 МБ) — обработка в памяти.
* Кодировки: `utf-8` с fallback `cp1251`.
* Рейтинг: `[0, 5]`, пустое значение игнорируется при среднем.

