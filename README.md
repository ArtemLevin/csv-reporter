### `README.md`

````markdown
# CSV Rating Reporter

Инструмент командной строки для объединения CSV-файлов и генерации отчёта по среднему рейтингу брендов.

---
## Demo

![Demo run](https://github.com/ArtemLevin/csv-reporter/blob/main/static/demo_01.png?raw=1)
![Demo test](https://github.com/ArtemLevin/csv-reporter/blob/main/static/demo_02.png?raw=1)

---

## Быстрый запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/ArtemLevin/csv-reporter.git
cd csv-reporter
````

### 2. Установка окружения и зависимостей

```bash
make install
```

Создаётся виртуальное окружение `.venv` и устанавливаются все зависимости.

---

## Пример запуска

### 3. Демонстрация

```bash
make demo
```

Будут созданы файлы:

```
examples/products_1.csv
examples/products_2.csv
examples/demo_output.txt
```

Просмотр результата:

```bash
cat examples/demo_output.txt
```

Ожидаемый вывод:

```
| brand   |   avg_rating |   items |
|---------|--------------|---------|
| apple   |         4.75 |       2 |
| samsung |         4.60 |       1 |
| google  |         4.50 |       1 |
| lenovo  |         4.40 |       1 |
```

---

## Пользовательский запуск

```bash
make run FILES="path/to/file1.csv path/to/file2.csv"
```

Параметры:

| Переменная | По умолчанию     | Назначение       |
| ---------- | ---------------- | ---------------- |
| `REPORT`   | `average-rating` | Тип отчёта       |
| `SORT`     | `avg_rating`     | Поле сортировки  |
| `LIMIT`    | —                | Количество строк |
| `TABLEFMT` | `github`         | Формат таблицы   |

Пример:

```bash
make run FILES="data1.csv data2.csv" SORT=brand TABLEFMT=grid
```

---

## Тесты

```bash
make test
```

Покрытие:

```bash
make cov
```

---

## Очистка

```bash
make clean
```

---

Для проверки работоспособности используйте `make demo`.
Для собственных данных используйте `make run` с вашими CSV-файлами.

```
```
