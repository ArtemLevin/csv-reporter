"""
Presentation (table formatting) tests for TablePresenter.

Назначение:
- Проверяет сортировку, ограничение количества строк и округление значений.
- Валидирует, что формат соответствует ожиданиям (заголовки/колонки, порядок).

Подход:
- Создаём список BrandStats вручную — без агрегации/CSV (SRP).
- Проверяем разные поля сортировки и limit.
"""

from __future__ import annotations

from csv_reporter.model import BrandStats
from csv_reporter.presenter import TablePresenter


def _mk_rows() -> list[BrandStats]:
    """Утилита: фиксированный набор DTO для тестов форматирования."""
    return [
        BrandStats(brand="alpha", avg_rating=4.251, items=3),
        BrandStats(brand="gamma", avg_rating=3.999, items=10),
        BrandStats(brand="beta", avg_rating=4.75, items=2),
    ]


def test_sort_by_avg_rating_desc_default():
    """По умолчанию сортируем по avg_rating по убыванию, округление до 2 знаков."""
    presenter = TablePresenter()
    out = presenter.render_brand_stats(_mk_rows())
    # Ожидаемый порядок: beta (4.75), alpha (4.25), gamma (4.00 после округления)
    beta_pos = out.find("beta")
    alpha_pos = out.find("alpha")
    gamma_pos = out.find("gamma")
    assert beta_pos < alpha_pos < gamma_pos
    # Проверяем округление:
    assert "4.75" in out
    assert "4.25" in out
    assert "4.00" in out


def test_sort_by_brand_ascending():
    """Сортировка по полю brand (по алфавиту), убывание=False (прямой порядок)."""
    presenter = TablePresenter()
    out = presenter.render_brand_stats(
        _mk_rows(),
        sort_by="brand",
        descending=False,
    )
    # Ожидаем: alpha, beta, gamma
    alpha_pos = out.find("alpha")
    beta_pos = out.find("beta")
    gamma_pos = out.find("gamma")
    assert alpha_pos < beta_pos < gamma_pos


def test_sort_by_items_then_limit_two():
    """Сортировка по items (по убыванию) и ограничение вывода до 2 строк."""
    presenter = TablePresenter()
    out = presenter.render_brand_stats(
        _mk_rows(),
        sort_by="items",
        descending=True,
        limit=2,
    )
    # gamma(items=10) должна быть первой; всего 2 строки данных
    assert "gamma" in out
    # Подсчитываем количество разделителей строк '|' c данными (не считаем заголовок).
    # Формат 'github' рисует таблицу с линиями; проще проверить наличие второй строки бренда.
    assert "alpha" in out or "beta" in out
    # Но третьего бренда быть не должно
    remaining = {"alpha", "beta"} - {b for b in ["alpha", "beta"] if b in out}
    assert len(remaining) == 1  # ровно один из alpha/beta отсутствует => 2 строки данных
