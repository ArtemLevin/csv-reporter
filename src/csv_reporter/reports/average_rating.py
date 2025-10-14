"""
Average Rating report implementation.

Назначение:
- Реализация отчёта "average-rating": считает средний рейтинг по брендам.
- Делегирует вычисления AggregatorService, сам не содержит бизнес-математики.

Почему так:
- SRP: отчёт отвечает за выбор нужной агрегации и преобразование к общему формату вывода.
- OCP: новые отчёты добавляются как новые классы, не меняя существующий код CLI.
- DIP: зависимость на AggregatorService передаётся через конструктор (удобно подменять в тестах).
"""

from __future__ import annotations

from typing import Sequence

from ..aggregator import AggregatorService
from ..model import BrandStats, Dataset
from .base import Report


class AverageRatingReport(Report):
    """Отчёт по среднему рейтингу брендов."""

    NAME = "average-rating"

    def __init__(self, aggregator: AggregatorService | None = None) -> None:
        """
        Args:
            aggregator: Сервис агрегации; по умолчанию создаётся дефолтный.

        Комментарий (DIP):
            - Через параметр конструктора можно передать тестовый/моковый агрегатор,
              не изменяя код класса (поддержка тестируемости и SOLID).
        """
        self._aggregator = aggregator or AggregatorService()

    def generate(self, dataset: Dataset) -> Sequence[BrandStats]:
        """
        Построить отчёт.

        Args:
            dataset: Набор продуктов для анализа.
        Returns:
            Sequence[BrandStats]: Список статистик по брендам.
        """
        # Вся логика агрегации инкапсулирована в сервисе — отчёт лишь делегирует вызов.
        return self._aggregator.compute_brand_avg_rating(dataset)
