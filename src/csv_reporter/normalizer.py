"""
Normalization helpers for CSV values (brand, price, rating).

Назначение:
- Функции предобработки и безопасного парсинга строковых значений из CSV.
- Никакой IO/CSV здесь нет — только преобразование отдельных полей.

Функции:
- normalize_brand(raw: str) -> str
- parse_price(raw: str) -> float
- parse_rating(raw: str) -> float | None

Политики:
- Бренд приводится к lower-case, лишние пробелы убираются, множественные пробелы схлопываются.
- Цена парсится из строк с возможными разделителями (пробелы, запятые как десятичные),
  символы валют удаляются. Требование: price >= 0.
- Рейтинг: допускается пустое значение → None; числовой диапазон [0, 5] включительно.
"""

from __future__ import annotations

import re
from typing import Optional

from .errors import DataError


# Предкомпилированные регулярки — быстрее и читаемее в коде
_CURRENCY_CHARS = re.compile(r"[^\d.,\- ]")  # всё, что не цифра/знак/разделители — удаляем
_MULTI_SPACE = re.compile(r"\s+")
_THOUSANDS_SEP = re.compile(r"(?<=\d)[\s_](?=\d{3}\b)")  # 12 345 -> 12345, 12_345 -> 12345


def normalize_brand(raw: str) -> str:
    """
    Normalize brand name.

    Args:
        raw: Исходная строка бренда (как из CSV).
    Returns:
        str: Нормализованное имя бренда в нижнем регистре без лишних пробелов.
    Raises:
        DataError: Если после нормализации строка пуста.

    Почему так:
        - В отчётах критично консистентное сравнение брендов.
        - Здесь не делаем "синонимизацию" (типа 'H&M' vs 'hm') — это предмет
          бизнес-правил конкретного проекта; оставляем простую нормализацию.
    """
    # Удаляем управляющие/непечатаемые символы по краям и схлопываем внутренние пробелы
    s = raw.strip()
    s = _MULTI_SPACE.sub(" ", s)
    s = s.lower()
    if not s:
        raise DataError("Empty brand after normalization")
    return s


def parse_price(raw: str) -> float:
    """
    Parse price from a human-friendly string into a non-negative float.

    Args:
        raw: Строка с ценой (может содержать пробелы, разделители тысяч, валютные символы).
    Returns:
        float: Цена >= 0.
    Raises:
        DataError: Если не удаётся распарсить или цена < 0.

    Правила:
        - Удаляем валютные символы (₽, $, €, и т.п.).
        - Удаляем разделители тысяч: пробелы/подчёркивания между цифрами.
        - Поддерживаем десятичные разделители точка ИЛИ запятая ("," -> ".").
        - Не округляем здесь: округление/форматирование — задача presenter.
    """
    s = raw.strip()
    if not s:
        raise DataError("Price is empty")

    # Удаляем валютные символы и любые посторонние буквы (оставляем цифры/знаки/., пробелы)
    s = _CURRENCY_CHARS.sub("", s)

    # Удаляем разделители тысяч "12 345" или "12_345" -> "12345"
    s = _THOUSANDS_SEP.sub("", s)

    # Заменяем запятые на точку как десятичный разделитель (локаль-независимо)
    s = s.replace(",", ".")

    try:
        value = float(s)
    except ValueError as exc:
        raise DataError(f"Invalid price: {raw!r}") from exc

    if value < 0:
        raise DataError(f"Negative price is not allowed: {value}")

    return value


def parse_rating(raw: str) -> Optional[float]:
    """
    Parse rating into a float in [0, 5] or None if missing.

    Args:
        raw: Строка с рейтингом; допускаются пустые значения.
    Returns:
        float | None: Число из диапазона [0, 5] или None, если рейтинг отсутствует.
    Raises:
        DataError: Если значение выходит из диапазона или не число.

    Политика:
        - Пустое поле/пробелы -> None (означает «нет валидного рейтинга»).
        - Допускаем запятую как десятичный разделитель.
        - Не округляем здесь; среднее и форматирование выполняет презентационный слой.
    """
    s = raw.strip()
    if not s:
        return None

    # Допускаем редкие варианты, где вместо числа записано "N/A" и т.п.
    if s.lower() in {"na", "n/a", "none", "null"}:
        return None

    # Заменяем запятую на точку (локаль-независимый парсинг)
    s = s.replace(",", ".")

    try:
        value = float(s)
    except ValueError as exc:
        raise DataError(f"Invalid rating: {raw!r}") from exc

    if not (0.0 <= value <= 5.0):
        raise DataError(f"Rating out of range [0, 5]: {value}")

    return value
