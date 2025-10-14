"""
Tests for ReportRegistry and report classes (average-rating).

Назначение:
- Проверяет корректность регистрации и создания отчётов через ReportRegistry.
- Проверяет поведение AverageRatingReport: делегирование AggregatorService.
- Гарантирует, что расширяемость через OCP работает без модификации CLI.

Подход:
- Используем reset_default_registry() для изоляции тестов.
- Создаём временный фейковый отчёт для проверки регистрации.
- Мокаем AggregatorService, чтобы убедиться, что вызов делегируется.
"""

from __future__ import annotations

import pytest

from csv_reporter.aggregator import AggregatorService
from csv_reporter.errors import ReportNotFoundError
from csv_reporter.model import Dataset
from csv_reporter.reports.average_rating import AverageRatingReport
from csv_reporter.reports.base import Report
from csv_reporter.reports.registry import (
    ReportRegistry,
    get_default_registry,
    reset_default_registry,
)


def test_registry_register_and_create_works(monkeypatch):
    """Регистрируем новый отчёт и создаём его экземпляр."""
    reg = ReportRegistry()

    class DummyReport(Report):
        NAME = "dummy"

        def generate(self, dataset: Dataset):  # pragma: no cover
            return []

    reg.register(DummyReport)
    created = reg.create("dummy")
    assert isinstance(created, DummyReport)
    assert "dummy" in reg.available()

    # Повторная регистрация того же имени должна вызвать ошибку
    with pytest.raises(ValueError):
        reg.register(DummyReport)


def test_registry_unknown_report_raises():
    """Неизвестное имя вызывает ReportNotFoundError."""
    reg = ReportRegistry()
    with pytest.raises(ReportNotFoundError):
        reg.create("nope")


def test_default_registry_lazy_load_and_reset(monkeypatch):
    """get_default_registry лениво создаёт экземпляр и регистрирует average-rating."""
    reset_default_registry()
    reg1 = get_default_registry()
    names = reg1.available()
    assert "average-rating" in names

    # После сброса создаётся новый объект
    reset_default_registry()
    reg2 = get_default_registry()
    assert reg1 is not reg2


def test_average_rating_report_delegates_to_aggregator(monkeypatch):
    """AverageRatingReport вызывает AggregatorService.compute_brand_avg_rating."""
    called = {}

    class FakeAgg(AggregatorService):
        def compute_brand_avg_rating(self, dataset: Dataset):  # type: ignore[override]
            called["ok"] = True
            return ["stub-result"]

    ds = Dataset()
    rep = AverageRatingReport(aggregator=FakeAgg())
    out = rep.generate(ds)
    assert called["ok"]
    assert out == ["stub-result"]
