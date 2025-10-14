"""
CLI argument & wiring tests for CSV Rating Reporter.

Назначение:
- Проверяет базовое поведение CLI-слоя: флаги, коды выхода, сообщения об ошибках.
- Не тестирует низкоуровневые детали агрегации (для этого есть отдельные тесты).

Подход:
- Импортируем `run` из `csv_reporter.cli` и вызываем напрямую (быстро и детерминированно).
- Перехватываем stdout/stderr через `capsys`.
- Временные CSV создаём в `tmp_path`, чтобы не зависеть от фикстур/репозитория.

Почему так:
- Тесты CLI должны быть быстрыми и изолированными, без запуска подпроцессов — проще отлаживать.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from csv_reporter import __version__
from csv_reporter.cli import run


def _write_csv(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    """Утилита: записать CSV с нужными заголовками и строками."""
    header = "name,brand,price,rating\n"
    body = "\n".join(",".join(r) for r in rows) + ("\n" if rows else "")
    path.write_text(header + body, encoding="utf-8")


def test_version_flag_prints_version_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """--version печатает версию и возвращает 0."""
    code = run(["--version"])
    out = capsys.readouterr().out
    assert code == 0
    assert __version__ in out


def test_no_files_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Отсутствие --files приводит к коду 1 и сообщению об ошибке."""
    code = run([])
    captured = capsys.readouterr()
    assert code == 1
    assert "Error:" in captured.err
    assert "No input files provided" in captured.err


def test_negative_limit_is_rejected(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Отрицательный --limit приводит к коду 1 и корректному сообщению."""
    csv1 = tmp_path / "a.csv"
    _write_csv(csv1, [("n1", "BrandA", "10.0", "4.0")])

    code = run(["--files", str(csv1), "--limit", "-1"])
    captured = capsys.readouterr()
    assert code == 1
    assert "--limit must be >= 0" in captured.err


def test_unknown_report_returns_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Неизвестный отчёт (OCP) корректно сообщает об ошибке и код 1."""
    csv1 = tmp_path / "a.csv"
    _write_csv(csv1, [("n1", "BrandA", "10.0", "4.0")])

    code = run(["--files", str(csv1), "--report", "unknown"])
    captured = capsys.readouterr()
    assert code == 1
    assert "Unknown report" in captured.err


def test_successful_run_prints_table(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Успешный сценарий:
    - Два CSV с несколькими брендами.
    - Ожидаем корректную таблицу в stdout и код 0.

    Комментарий:
    - Здесь проверяем не точные числа с округлением, а наличие заголовков и брендов,
      чтобы тест не был хрупким к форматированию.
    """
    csv1 = tmp_path / "p1.csv"
    csv2 = tmp_path / "p2.csv"

    _write_csv(
        csv1,
        [
            ("n1", "BrandA", "10.00", "4.5"),
            ("n2", "BrandB", "20.00", "3.5"),
        ],
    )
    _write_csv(
        csv2,
        [
            ("n3", "BrandA", "12.00", "5"),
            ("n4", "BrandC", "30.00", ""),  # пустой рейтинг -> игнорируется в среднем
        ],
    )

    code = run(["--files", str(csv1), str(csv2), "--report", "average-rating", "--sort", "brand"])
    captured = capsys.readouterr()
    assert code == 0
    out = captured.out
    # Проверяем заголовки таблицы tabulate и наличие брендов
    assert "brand" in out and "avg_rating" in out and "items" in out
    assert "branda" in out  # нормализованный бренд в нижнем регистре
    assert "brandb" in out
    assert "brandc" not in out or " 0 " not in out  # BrandC без валидных рейтингов не должен появляться
