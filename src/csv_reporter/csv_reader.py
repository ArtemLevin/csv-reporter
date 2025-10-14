"""
CSV reader with schema validation and tolerant decoding.

Назначение:
- Безопасно читает один или несколько CSV-файлов, валидирует заголовки,
  нормализует поля и формирует Dataset из Product.
- Не содержит бизнес-агрегации и форматирования — только ввод и базовая валидация.

Публичное API:
- class CSVReader:
    - load(files: list[str]) -> Dataset

Поведение:
- Ожидаемые столбцы: name, brand, price, rating (порядок не важен, регистр заголовков не важен).
- Кодировка: пытаемся 'utf-8', при ошибке — fallback на 'cp1251'.
- Стратегия ошибок:
    - Отсутствуют обязательные столбцы → SchemaError.
    - Некорректная строка (цена/рейтинг/бренд) → DataError (с указанием файла/номера строки).
      *Компромисс:* при DataError мы прерываем процесс, чтобы не скрывать проблемные данные.
      При желании в будущем можно добавить флаг "--skip-errors".
"""

from __future__ import annotations

import csv
import os
from typing import Dict, Iterable, List, Tuple

from .errors import DataError, SchemaError
from .logging_utils import LogTimer, get_logger
from .model import Dataset, Product
from .normalizer import normalize_brand, parse_price, parse_rating

_LOG = get_logger(__name__)

_REQUIRED_COLUMNS = ("name", "brand", "price", "rating")


class CSVReader:
    """
    Reader сервиса данных для входных CSV-файлов.

    Комментарии по SOLID:
    - SRP: модуль/класс отвечает только за чтение/нормализацию входных данных.
    - OCP: схема валидации сделана массово-простой; при расширении (новые поля) можно
           переопределить проверку или добавить новую реализацию ридера.
    - DIP: завязка на stdlib; абстрактный интерфейс DI не вводим, т.к. подмена
           достигается через мок-объекты в тестах (практичный компромисс).
    """

    def load(self, files: List[str]) -> Dataset:
        """
        Загрузить и слить несколько CSV в общий Dataset.

        Args:
            files: Список путей к CSV-файлам.
        Returns:
            Dataset: Контейнер с Product.
        Raises:
            SchemaError: Если хотя бы в одном файле отсутствуют нужные столбцы.
            DataError: Если обнаружены некорректные значения в строке.
            FileNotFoundError: Если файл не существует.
            PermissionError: Если нет прав на чтение файла.
        """
        dataset = Dataset()
        canonical_files = [self._ensure_file(p) for p in files]
        if not canonical_files:
            raise SchemaError("No input files provided")

        for path in canonical_files:
            with LogTimer(_LOG, f"read_csv {os.path.basename(path)}"):
                self._read_single(path, dataset)

        _LOG.info("Total rows loaded: %d", len(dataset))
        return dataset

    # -------------------------- internal helpers --------------------------

    def _ensure_file(self, path: str) -> str:
        """
        Проверить существование файла и вернуть его абсолютный путь.

        Raises:
            FileNotFoundError, IsADirectoryError, PermissionError
        """
        abspath = os.path.abspath(path)
        if not os.path.exists(abspath):
            raise FileNotFoundError(f"File not found: {path}")
        if not os.path.isfile(abspath):
            raise IsADirectoryError(f"Not a file: {path}")
        # Дополнительно проверим разрешения на чтение
        if not os.access(abspath, os.R_OK):
            raise PermissionError(f"File is not readable: {path}")
        return abspath

    def _open_with_fallback(self, path: str):
        """
        Открыть файл с попыткой utf-8 и fallback на cp1251.

        Почему именно так:
            - По SRS ожидаем UTF-8, но часть CSV из Windows может быть CP1251.
            - Не пытаемся угадать локаль автоматически (лишняя сложность/зависимости).
        """
        try:
            return open(path, "r", encoding="utf-8", newline="")  # noqa: PTH123
        except UnicodeDecodeError:
            _LOG.info("Fallback to cp1251 for %s", os.path.basename(path))
            return open(path, "r", encoding="cp1251", newline="")  # noqa: PTH123

    def _read_single(self, path: str, dataset: Dataset) -> None:
        """
        Прочитать один CSV и добавить его строки в Dataset.
        """
        with self._open_with_fallback(path) as fh:
            reader = csv.DictReader(fh)
            header_map = self._validate_and_map_headers(reader.fieldnames, path)
            line_no = 1  # счётчик для данных, не считая заголовков
            for row in reader:
                line_no += 1
                product = self._parse_row(row, header_map, path, line_no)
                dataset.add(product)

            _LOG.info("Rows read from %s: %d", os.path.basename(path), line_no - 1)

    def _validate_and_map_headers(
        self, fieldnames: Iterable[str] | None, path: str
    ) -> Dict[str, str]:
        """
        Проверить наличие требуемых столбцов, вернуть map "canonical -> actual".

        Args:
            fieldnames: Заголовки из CSV.
        Returns:
            Dict[str, str]: Отображение канонического имени на реальное имя из файла.
        Raises:
            SchemaError: Если любого из обязательных столбцов нет.
        """
        if not fieldnames:
            raise SchemaError(f"Missing headers in CSV: {path}")

        # Нормализуем регистр/пробелы для сравнения, но сохраняем исходное имя для доступа к row
        normalized: Dict[str, str] = {}
        by_lower = {h.strip().lower(): h for h in fieldnames}

        for required in _REQUIRED_COLUMNS:
            actual = by_lower.get(required)
            if not actual:
                raise SchemaError(
                    f"Required column '{required}' not found in {path}; found: {list(fieldnames)}"
                )
            normalized[required] = actual

        return normalized

    def _parse_row(
        self, row: Dict[str, str], headers: Dict[str, str], path: str, line_no: int
    ) -> Product:
        """
        Преобразовать строку CSV в Product с нормализацией.

        Raises:
            DataError: С подробным указанием файла и строки для диагностируемости.
        """
        try:
            name_raw = row.get(headers["name"], "").strip()
            brand_raw = row.get(headers["brand"], "")
            price_raw = row.get(headers["price"], "")
            rating_raw = row.get(headers["rating"], "")

            if not name_raw:
                raise DataError("Empty product name")

            brand = normalize_brand(brand_raw)
            price = parse_price(price_raw)
            rating = parse_rating(rating_raw)

            return Product(name=name_raw, brand=brand, price=price, rating=rating)
        except (DataError, KeyError) as exc:
            # Добавляем контекст файла и номера строки — крайне полезно при разборе логов
            raise DataError(f"{path}:{line_no}: {exc}") from exc
