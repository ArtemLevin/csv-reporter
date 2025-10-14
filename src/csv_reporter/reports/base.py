"""
Report abstraction (base class) for CSV Rating Reporter.

Назначение:
- Определяет минимальный контракт для отчётов: метод `generate(dataset)`.
- Базовый класс не знает о CLI/презентации, только о доменных DTO.

Дизайн:
- Единый маленький интерфейс (Interface Segregation): только `generate`.
- Идентификатор отчёта задаётся через атрибут класса `NAME` (строка).
- Возвращаемый тип — последовательность `BrandStats` для совместимости с presenter.

Компромиссы:
- Без generics/Protocol — здесь достаточно ABC, чтобы не усложнять типизацию.
- Если появятся отчёты с иным выходным форматом, presenter сможет поддержать ветку
  форматирования по типу элементов, но до тех пор держим единый формат.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from ..model import BrandStats, Dataset


class Report(ABC):
    """
    Абстракция отчёта.

    Атрибуты класса:
        NAME: Строковый идентификатор отчёта (используется в реестре/CLI).

    Методы:
        generate(dataset: Dataset) -> Sequence[BrandStats]
    """

    # Идентификатор должен быть переопределён в наследнике.
    NAME: str = "base-report"

    @abstractmethod
    def generate(self, dataset: Dataset) -> Sequence[BrandStats]:
        """
        Построить отчёт по данным.

        Args:
            dataset: Набор продуктов для анализа.
        Returns:
            Sequence[BrandStats]: Агрегированные метрики по брендам.
        """
        raise NotImplementedError
