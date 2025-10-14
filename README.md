### `README.md`

````markdown
# CSV Rating Reporter (average-rating)

> Назначение: краткая документация по установке, запуску, архитектурным решениям и вкладу в проект.  
> Данный файл **не содержит исполняемого кода** — только инструкции и пояснения.

## Кратко
CLI-утилита для локальной консолидации CSV-файлов и построения отчёта среднего рейтинга по брендам.  
Только stdlib + `tabulate`. Без сетевых вызовов и внешних сервисов.

## Установка
```bash
# из локального исходника
pip install -e .
# или сборка колеса
python -m build && pip install dist/csv_rating_reporter-*.whl
````

## Быстрый старт

Подготовьте CSV с заголовками: `name,brand,price,rating` (регистр заголовков не важен).

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

Запуск:

```bash
csvreporter --files products_1.csv products_2.csv --report average-rating
```

Пример вывода:

```
| brand   |   avg_rating |   items |
|---------|---------------|---------|
| apple   |          4.75 |       2 |
| samsung |          4.60 |       1 |
| google  |          4.50 |       1 |
| lenovo  |          4.40 |       1 |
```

Полезные флаги:

```bash
# сортировка по бренду, не по рейтингу
csvreporter --files *.csv --sort brand --report average-rating

# ограничить вывод до 3 строк
csvreporter --files *.csv --limit 3

# подробные логи и версия
csvreporter --files *.csv --debug
csvreporter --version
```

Коды выхода:

* `0` — успех;
* `1` — ошибки (некорректные аргументы, схема CSV, данные, доступ к файлам).

Сообщения об ошибках печатаются на `stderr` в формате: `Error: <описание>`.

## Архитектура (обзор)

* **CLI**: `src/csv_reporter/cli.py` — парсер аргументов, связывание слоёв, коды выхода.
* **Data**: `csv_reader.py` — валидация заголовков, чтение CSV (UTF-8 → fallback CP1251), нормализация.
* **Domain**: `model.py` (DTO), `aggregator.py` (средние по брендам).
* **Reports**: `reports/base.py` (абстракция), `reports/average_rating.py` (реализация), `reports/registry.py` (реестр).
* **Presentation**: `presenter.py` — форматирование через `tabulate`.
* **Infra**: `errors.py` (иерархия исключений), `logging_utils.py` (stderr-логи, таймер).

### Компромиссы:

* Не используем pandas/DI-контейнеры — избыточно для масштаба задачи.
* При `DataError` чтение прерывается (fail-fast); опциональный `--skip-errors` можно добавить в будущих версиях.

## Разработка

```bash
# установка зависимостей для разработки
pip install -e ".[dev]"

# линт, типы, тесты, покрытие
ruff check .
ruff format .
mypy src
pytest
pytest --cov=csv_reporter --cov-report=term-missing
```

### Структура репозитория (сводно)

```
src/csv_reporter/
  cli.py            # CLI и оркестрация слоёв
  csv_reader.py     # чтение/валидация CSV, нормализация
  model.py          # DTO: Product, BrandStats, Dataset
  aggregator.py     # бизнес-агрегация по брендам
  presenter.py      # табличный вывод (tabulate)
  errors.py         # исключения домена/CLI
  logging_utils.py  # логи на stderr, простой таймер
  reports/
    base.py
    average_rating.py
    registry.py
tests/
  *.py              # pytest: CLI, агрегация, форматирование, реестр
```

## Расширение отчётов

Пример добавления отчёта `average-price`:

1. Создайте `reports/average_price.py` c классом `AveragePriceReport(Report)`.
2. Зарегистрируйте его в `get_default_registry()` (или вызовите `register` из клиентского кода).
3. Запускайте: `--report average-price`.

## Ограничения

* До ~10k строк (≈2 МБ) комфортно обрабатывается в памяти.
* Кодировки: `utf-8` с fallback `cp1251`.
* Рейтинг должен быть в диапазоне `[0, 5]`, пустое значение допускается (игнорируется при среднем).



