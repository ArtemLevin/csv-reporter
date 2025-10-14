"""
Lightweight logging helpers for CSV Rating Reporter.

Назначение:
- Единая точка настройки логирования на stderr.
- Утилита-таймер для простого профилирования критических участков.

Типы:
- set_up_logging(debug: bool) -> None — конфигурирует root-логгер.
- get_logger(name: str) -> logging.Logger — возвращает именованный логгер.
- LogTimer — контекстный менеджер, логирующий длительность блока кода.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass


def set_up_logging(debug: bool = False) -> None:
    """
    Configure root logger for CLI.

    Args:
        debug: Если True — уровень DEBUG, иначе INFO.

    Компромисс:
    - Используем базовую настройку logging без сторонних форматтеров,
      т.к. требование проекта — минимум зависимостей.
    - Формат простой и читаемый: "[LEVEL] message".
    """
    level = logging.DEBUG if debug else logging.INFO

    # Важно: basicConfig имеет эффект только один раз за процесс;
    # это ожидаемо для CLI (запуск — один процесс).
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        stream=sys.stderr,
        force=True,  # перезаписываем конфиг на случай повторной инициализации в тестах
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.

    Args:
        name: Имя логгера (обычно __name__ модуля).
    Returns:
        logging.Logger: Именованный логгер, наследующий конфигурацию root.
    """
    return logging.getLogger(name)


@dataclass
class LogTimer:
    """
    Context manager for timing code sections and logging duration.

    Пример:
        with LogTimer(logger, "read_csv"):
            read_csv_files(paths)

    Args:
        logger: Логгер, куда писать сообщение.
        label: Короткая метка операции.
        level: Уровень логирования (по умолчанию INFO).

    Поведение:
        - В __enter__ запоминаем perf_counter().
        - В __exit__ логируем длительность в миллисекундах.
    """

    logger: logging.Logger
    label: str
    level: int = logging.INFO

    def __enter__(self) -> "LogTimer":
        # Запоминаем стартовое время (быстрые монотонные часы)
        self._t0 = time.perf_counter()  # type: ignore[attr-defined]
        # В debug-режиме может быть полезно отметить старт
        self.logger.log(self.level, f"{self.label}...")  # простой индикатор начала
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        dt_ms = (time.perf_counter() - self._t0) * 1000.0  # type: ignore[attr-defined]
        # Если был эксепшн — добавляем пометку "failed", иначе "done"
        status = "failed" if exc_type is not None else "done"
        # Логируем результат с длительностью
        self.logger.log(self.level, f"{self.label}: {status} in {dt_ms:.1f} ms")


# Пояснение по SRP:
# - Модуль отвечает только за логирование и простую измерительную утилиту.
# - Ни чтения CSV, ни агрегирования — здесь нет.
# - Таймер включён сюда осознанно: observability относится к логированию, поэтому это не нарушает SRP.
