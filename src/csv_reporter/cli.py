"""
Command-line interface for CSV Rating Reporter.

Назначение:
- Парсит аргументы, настраивает логирование, связывает слои (CSVReader → Report → Presenter).
- Оборачивает ошибки в единый формат "Error: <msg>" и корректные коды выхода.

Публичное API:
- main() -> None — точка входа для консольного сценария.
- run(argv: list[str] | None) -> int — исполняет CLI и возвращает exit code (удобно для тестов).

Аргументы:
- --files FILE [FILE ...] — входные CSV (обязателен хотя бы один).
- --report NAME — имя отчёта (по умолчанию: "average-rating").
- --sort {brand,avg_rating,items} — поле сортировки вывода (по умолчанию avg_rating).
- --limit N — ограничение числа строк (опционально).
- --tablefmt FMT — формат вывода tabulate (github|simple|plain|grid|fancy_grid|psql|tsv).
- --debug — подробные логи на stderr.
- --version — вывести версию и завершить.

Компромиссы:
- DIP — внедряем зависимости явно параметрами/локальными инстансами (без DI-контейнера).
- OCP — набор отчётов расширяем через ReportRegistry, CLI остаётся неизменным.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__
from .csv_reader import CSVReader
from .errors import CliError, CsvReporterError
from .logging_utils import get_logger, set_up_logging
from .presenter import SortField, TablePresenter
from .reports.registry import get_default_registry

_LOG = get_logger(__name__)

# Разрешённые форматы табличного вывода (ограниченный whitelisting для предсказуемости UX)
_ALLOWED_TABLEFMTS = (
    "github",
    "simple",
    "plain",
    "grid",
    "fancy_grid",
    "psql",
    "tsv",
)


def _build_parser() -> argparse.ArgumentParser:
    """
    Построить argparse-парсер без побочных эффектов.

    Возвращаем отдельный объект — так проще тестировать help/валидацию.
    """
    parser = argparse.ArgumentParser(
        prog="csvreporter",
        description="Consolidate CSV files and show brand average rating report.",
    )

    parser.add_argument(
        "--files",
        metavar="FILE",
        nargs="+",
        required=False,  # проверим вручную, чтобы контролировать формат ошибки
        help="Paths to CSV files to read (at least one).",
    )
    parser.add_argument(
        "--report",
        default="average-rating",
        help='Report name (default: "average-rating").',
    )
    parser.add_argument(
        "--sort",
        choices=("brand", "avg_rating", "items"),
        default="avg_rating",
        help="Sort field for output table.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for number of rows in the output.",
    )
    parser.add_argument(
        "--tablefmt",
        choices=_ALLOWED_TABLEFMTS,
        default="github",
        help=f"Tabulate format for output (default: github). Allowed: {', '.join(_ALLOWED_TABLEFMTS)}.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit.",
    )

    return parser


def run(argv: Optional[List[str]] = None) -> int:
    """
    Выполнить CLI-логику и вернуть код выхода.

    Args:
        argv: Список аргументов без имени программы; если None — берём sys.argv[1:].
    Returns:
        int: 0 при успехе, 1 при ошибке.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Быстрый выход по версии — удобно в CI и скриптах.
    if args.version:
        print(__version__)
        return 0

    # Настраиваем логирование как можно раньше.
    set_up_logging(debug=bool(args.debug))

    # Валидация наличия файлов
    files: Optional[List[str]] = args.files
    if not files:
        _emit_error("No input files provided. Use --files FILE [FILE ...].")
        return 1

    sort_by: SortField = args.sort  # Literal-сигнатура дополнительно контролируется presenter'ом.
    limit: Optional[int] = args.limit
    if limit is not None and limit < 0:
        _emit_error("--limit must be >= 0")
        return 1

    tablefmt: str = args.tablefmt
    report_name: str = args.report

    try:
        # 1) Читаем и нормализуем CSV → Dataset
        reader = CSVReader()
        dataset = reader.load(files)

        # 2) Получаем отчёт из реестра и генерируем агрегированные DTO
        registry = get_default_registry()
        report = registry.create(report_name)
        stats = report.generate(dataset)

        # 3) Форматируем и печатаем таблицу
        presenter = TablePresenter()
        table = presenter.render_brand_stats(
            stats, sort_by=sort_by, descending=True, limit=limit, tablefmt=tablefmt
        )
        print(table)
        return 0

    except CsvReporterError as err:
        # Единообразные ошибки домена/CLI
        _emit_error(str(err))
        return 1
    except (FileNotFoundError, PermissionError, IsADirectoryError) as err:
        _emit_error(str(err))
        return 1
    except Exception as err:  # крайний перехват на случай непредвиденных ошибок
        # В debug-режиме полезно видеть traceback, но по требованиям выводим короткое сообщение.
        _LOG.exception("Unhandled error")  # в логи уходит traceback
        _emit_error(f"Unexpected error: {err}")
        return 1


def _emit_error(message: str) -> None:
    """
    Печать ошибки в RFC7807-подобном кратком формате.

    Почему так:
    - Для CLI достаточно "Error: <msg>" — легко парсить и стабильно тестировать.
    """
    sys.stderr.write(f"Error: {message}\n")


def main() -> None:
    """
    Точка входа для console_script.

    Ничего не возвращает — завершает процесс соответствующим кодом.
    """
    code = run()
    # Явно завершаем процесс — стандартный приём для CLI.
    raise SystemExit(code)
