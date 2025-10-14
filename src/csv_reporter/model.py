"""
Domain data models for CSV Rating Reporter.

Назначение:
- Описывает DTO уровня домена: Product, BrandStats и контейнер Dataset.
- Не содержит бизнес-логики чтения/агрегации — только структуру данных и лёгкие утилиты.

Типы:
- Product: единица входных данных CSV (rating может отсутствовать).
- BrandStats: агрегированная метрика по бренду.
- Dataset: коллекция продуктов с безопасным API для итерации и измерения.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional


@dataclass(slots=True)
class Product:
    """
    DTO для строки CSV.

    Args:
        name: Название продукта.
        brand: Название бренда (нормализация выполняется вне модели).
        price: Цена в денежной единице (нормализация/парсинг — вне модели).
        rating: Рейтинг [0..5] или None, если отсутствует/невалиден.

    Примечание:
        Валидация инвариантов (диапазоны и т.п.) выполняется в нормализаторе/агрегаторе.
        Здесь — только структура (SRP), чтобы не смешивать слои.
    """

    name: str
    brand: str
    price: float
    rating: Optional[float] = None  # None означает "нет валидного рейтинга"

    # Комментарий:
    #   Не реализуем __post_init__ с проверками — это сознательный компромисс.
    #   Проверки зависят от контекста парсинга (например, политика округления),
    #   поэтому они реализованы в normalizer.py / aggregator.py.


@dataclass(slots=True)
class BrandStats:
    """
    Агрегированная статистика по бренду.

    Args:
        brand: Имя бренда (уже нормализованное).
        avg_rating: Средний рейтинг по валидным записям [0..5].
        items: Количество учтённых элементов (шт.).
    """

    brand: str
    avg_rating: float
    items: int

    # Здесь не делаем вычислений и не храним промежуточные суммы —
    # только результат, чтобы DTO оставался простым и сериализуемым.


@dataclass
class Dataset:
    """
    Контейнер для доменных объектов Product.

    Предоставляет минимальный API коллекции:
    - добавление элементов,
    - итерация,
    - размер.

    Компромисс:
        Dataset — "тонкий" объект без бизнес-операций. Это упрощает тестирование
        и соблюдает SRP: загрузка/нормализация — в csv_reader/normalizer,
        агрегирование — в aggregator.
    """

    products: List[Product] = field(default_factory=list)

    def add(self, product: Product) -> None:
        """Добавить один продукт в набор."""
        self.products.append(product)

    def extend(self, items: Iterable[Product]) -> None:
        """Добавить несколько продуктов в набор."""
        self.products.extend(items)

    def __iter__(self) -> Iterator[Product]:
        """Итерируемся по продуктам в наборе."""
        return iter(self.products)

    def __len__(self) -> int:
        """Количество продуктов в наборе."""
        return len(self.products)
