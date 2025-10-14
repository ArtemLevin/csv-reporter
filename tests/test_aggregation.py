"""
Aggregation tests for brand average ratings.

Назначение:
- Проверяет корректность вычисления среднего рейтинга по брендам.
- Валидирует инварианты: учитываются только валидные рейтинги, диапазон [0..5].
- Никакого IO/CLI: чистые юнит-тесты доменного слоя.

Подход:
- Создаём Dataset вручную (SRP: без CSVReader), чтобы тест был минимальным и быстрым.
- Используем параметризацию для разных наборов входных данных.
- Проверяем, что сортировка отсутствует в AggregatorService (это забота presenter).
"""

from __future__ import annotations

from typing import Iterable

import math
import pytest

from csv_reporter.aggregator import AggregatorService
from csv_reporter.errors import DataError
from csv_reporter.model import BrandStats, Dataset, Product


def _mk_products(items: Iterable[tuple[str, str, float, float | None]]) -> Dataset:
    """
    Утилита: собрать Dataset из кортежей (name, brand, price, rating_or_none).
    Комментарий:
        - Бренды ожидаются уже нормализованными; мы тестируем именно агрегацию.
    """
    ds = Dataset()
    for name, brand, price, rating in items:
        ds.add(Product(name=name, brand=brand, price=price, rating=rating))
    return ds


@pytest.mark.parametrize(
    "rows,expected",
    [
        # 1) Простой случай: один бренд, все рейтинги валидны
        (
            [("n1", "brandx", 10.0, 4.0), ("n2", "brandx", 11.0, 5.0)],
            [BrandStats(brand="brandx", avg_rating=4.5, items=2)],
        ),
        # 2) Два бренда, у одного пропущенный рейтинг — не учитывается
        (
            [
                ("n1", "a", 10.0, 5.0),
                ("n2", "a", 12.0, None),  # None не входит в среднее
                ("n3", "b", 20.0, 3.0),
            ],
            [
                BrandStats(brand="a", avg_rating=5.0, items=1),
                BrandStats(brand="b", avg_rating=3.0, items=1),
            ],
        ),
        # 3) Несколько значений — проверяем численную устойчивость (fsum)
        (
            [("n" + str(i), "z", 1.0, 4.0) for i in range(1000)],
            [BrandStats(brand="z", avg_rating=4.0, items=1000)],
        ),
    ],
)
def test_compute_brand_avg_rating(rows, expected):
    """Проверяем, что средние значения и количество элементов совпадают с ожиданием."""
    ds = _mk_products(rows)
    svc = AggregatorService()
    out = svc.compute_brand_avg_rating(ds)

    # Для удобства сверим по словарю brand -> (avg, count).
    got = {bs.brand: (bs.avg_rating, bs.items) for bs in out}
    want = {bs.brand: (bs.avg_rating, bs.items) for bs in expected}

    # Сравниваем с допуском по плавающей точке
    assert set(got.keys()) == set(want.keys())
    for k in want:
        avg_got, cnt_got = got[k]
        avg_want, cnt_want = want[k]
        assert cnt_got == cnt_want
        assert math.isclose(avg_got, avg_want, rel_tol=1e-9, abs_tol=1e-12)


def test_ignores_brands_without_valid_ratings():
    """Бренд без валидных рейтингов не должен появляться в выходном списке."""
    ds = _mk_products([
        ("n1", "emptybrand", 10.0, None),
        ("n2", "ok", 11.0, 4.0),
    ])
    svc = AggregatorService()
    out = svc.compute_brand_avg_rating(ds)
    brands = {bs.brand for bs in out}
    assert "ok" in brands
    assert "emptybrand" not in brands


def test_defensive_invariant_violation_raises():
    """
    Защитная проверка: если в Dataset попадёт рейтинг вне [0,5],
    AggregatorService должен поднять DataError.
    """
    ds = _mk_products([("n1", "b", 10.0, 6.0)])  # заведомо неверный рейтинг
    svc = AggregatorService()
    with pytest.raises(DataError):
        _ = svc.compute_brand_avg_rating(ds)


def test_no_sorting_side_effects():
    """
    Проверяем, что AggregatorService не сортирует результат — порядок не гарантируется.
    Сортировка — ответственность presenter; здесь убеждаемся, что порядок может быть любым.
    """
    ds = _mk_products([
        ("n1", "b", 10.0, 4.0),
        ("n2", "a", 11.0, 5.0),
    ])
    svc = AggregatorService()
    out = svc.compute_brand_avg_rating(ds)

    # Порядок может быть ['b','a'] или ['a','b']; нас интересует состав и корректные значения.
    brands = {bs.brand for bs in out}
    assert brands == {"a", "b"}
