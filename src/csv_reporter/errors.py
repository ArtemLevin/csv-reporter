"""
Domain and CLI exception hierarchy for CSV Rating Reporter.

Назначение:
- Единообразные типы ошибок для домена, ввода/вывода и CLI.
- Чёткая грань: доменные ошибки не знают про argparse/CLI, а CLI ошибки не "протекают" в домен.

Design:
- Все ошибки наследуются от `CsvReporterError` (единая точка перехвата в верхнем уровне).
- `SchemaError` — некорректные заголовки/схема CSV.
- `DataError` — некорректные значения в строках (например, rating вне [0, 5]).
- `ReportNotFoundError` — запрос отчёта, которого нет в реестре.
- `CliError` — ошибки уровня CLI (некорректные аргументы, отсутствующие файлы и т.п.).

Типы аргументов и возвращаемых значений:
- Исключения не возвращают значения; содержат диагностическое сообщение (str).
"""

from __future__ import annotations


class CsvReporterError(Exception):
    """Base error for all reporter-related exceptions.

    Args:
        message: Человекочитаемое описание проблемы.
    """

    def __init__(self, message: str) -> None:
        # Простой контейнер для текста; без лишних полей, чтобы не усложнять обработку.
        super().__init__(message)


class SchemaError(CsvReporterError):
    """Raised when CSV schema (headers) is invalid.

    Пример: отсутствует колонка `rating` или неправильный порядок/название столбцов.
    """


class DataError(CsvReporterError):
    """Raised when a data row is invalid or cannot be normalized.

    Пример: отрицательная цена, рейтинг > 5, пустое название бренда.
    """


class ReportNotFoundError(CsvReporterError):
    """Raised when requested report name is not registered in the registry.

    Пример: пользователь передал `--report unknown-report`.
    """


class CliError(CsvReporterError):
    """Raised for CLI-level issues (arguments, file existence, permissions).

    Важно:
    - Эти ошибки формируются ближе к интерфейсу пользователя.
    - Доменные модули *не должны* возбуждать CliError (сохранение SRP).
    """
