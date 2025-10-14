"""
Domain aggregation logic (brand-level stats).

Назначение:
- Реализует чистые вычисления поверх Dataset: группировка по брендам и вычисление среднего рейтинга.
- Не знает о вводе/выводе, CLI или форматировании таблиц — только расчёты.

Публичное API:
- class AggregatorService:
    - compute_brand_avg_rating(dataset: Dataset) -> list[BrandStats]

Правила (инварианты):
- Среднее считается только по валидным рейтингам (rating != None), диапазон [0..5] уже гарантирован нормализатором.
- Колонка `items` — количество записей с валидным рейтингом, вошедших в среднее.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from .errors import DataError
from .model import BrandStats, Dataset, Product


@dataclass(slots=True)
class _Acc:
    """Внутренний аккумулятор для суммирования рейтингов по бренду."""

    sum_ratings: float = 0.0
    count: int = 0


class AggregatorService:
    """
    Сервис агрегации доменных данных.

    SOLID комментарии:
    - SRP: только расчёты/агрегирование. Ввод/вывод и форматирование вынесены в другие модули.
    - OCP: новые виды агрегаций добавляются как новые методы или через Report-реализации — без изменения существующих.
    - LSP: не вводим чрезмерных абстракций (нет "IStatisticsStrategy"), чтобы не усложнять простой сценарий.
    - DIP: зависимостей от внешних сервисов нет; для тестов легко подменять входной Dataset.
    """

    def compute_brand_avg_rating(self, dataset: Dataset) -> List[BrandStats]:
        """
        Сгруппировать продукты по бренду и посчитать средний рейтинг.

        Args:
            dataset: Набор продуктов.
        Returns:
            list[BrandStats]: По одному элементу на бренд.
        Raises:
            DataError: Если во входных данных обнаружен рейтинг вне диапазона [0..5]
                       (дополнительная защитная проверка; не должна срабатывать при корректном нормализаторе).
        """
        acc: Dict[str, _Acc] = {}

        for p in dataset:
            # Объяснение: нормализация выполнялась раньше; здесь — только аккуратная агрегация.
            rating: Optional[float] = p.rating
            if rating is None:
                continue  # пропускаем записи без валидного рейтинга

            # Дополнительная защитная проверка инварианта (на случай изменений нормализатора).
            if not (0.0 <= rating <= 5.0):
                raise DataError(f"Invariant violated: rating out of range [0, 5]: {rating}")

            bucket = acc.setdefault(p.brand, _Acc())
            # Используем math.fsum для численной устойчивости при суммировании большого числа элементов.
            bucket.sum_ratings = math.fsum([bucket.sum_ratings, rating])
            bucket.count += 1

        # Преобразуем аккумуляторы в DTO BrandStats
        out: List[BrandStats] = []
        for brand, bucket in acc.items():
            if bucket.count == 0:
                # Теоретически мы не создаём пустые бакеты, но оставим явную проверку.
                continue
            avg = bucket.sum_ratings / bucket.count
            out.append(BrandStats(brand=brand, avg_rating=avg, items=bucket.count))

        # Сортировку по умолчанию (например, по убыванию среднего) делаем в presenter,
        # чтобы не смешивать обязанности (SRP). Здесь возвращаем "как есть".
        return out
