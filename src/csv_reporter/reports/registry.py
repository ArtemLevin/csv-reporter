"""
Report registry (factory by report name).

Назначение:
- Хранит соответствие "имя отчёта → класс отчёта".
- Позволяет создать экземпляр отчёта по строковому идентификатору (используется CLI).
- Обеспечивает расширяемость без модификации существующего кода (OCP).

Публичное API:
- class ReportRegistry:
    - register(report_cls) -> None
    - create(name) -> Report
    - available() -> list[str]
- get_default_registry() -> ReportRegistry (ленивая инициализация)
- reset_default_registry() -> None (для тестов)
"""

from __future__ import annotations

from typing import Dict, List, Type

from .base import Report
from ..errors import ReportNotFoundError


class ReportRegistry:
    """
    Реестр отчётов (простая фабрика).

    Почему так (комментарии по SOLID/компромиссам):
    - SRP: класс отвечает только за регистрацию и создание отчётов по имени.
    - OCP: чтобы добавить новый отчёт, достаточно зарегистрировать его класс, не меняя код CLI.
    - DIP: CLI зависит от абстракции реестра/базового класса Report, а не от конкретных реализаций.
    - Компромисс: DI-контейнер не вводим; для нашего размера проекта достаточно явного реестра.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[Report]] = {}

    def register(self, report_cls: Type[Report]) -> None:
        """
        Зарегистрировать класс отчёта.

        Args:
            report_cls: Класс, наследующий Report, с атрибутом NAME (уникальным).
        Raises:
            ValueError: Если NAME пустой или уже зарегистрирован.
        """
        name = getattr(report_cls, "NAME", None)
        if not name or not isinstance(name, str):
            raise ValueError("Report class must define string NAME")
        key = name.strip().lower()
        if not key:
            raise ValueError("Report NAME must be non-empty")
        if key in self._registry:
            raise ValueError(f"Report already registered: {key}")
        self._registry[key] = report_cls

    def create(self, name: str) -> Report:
        """
        Создать экземпляр отчёта по имени.

        Args:
            name: Строковый идентификатор отчёта (регистр не важен).
        Returns:
            Report: Экземпляр соответствующего класса.
        Raises:
            ReportNotFoundError: Если отчёт с таким именем не зарегистрирован.
        """
        key = name.strip().lower()
        try:
            cls = self._registry[key]
        except KeyError as exc:
            raise ReportNotFoundError(f"Unknown report: {name!r}") from exc
        # Создаём без аргументов — конкретная реализация сама решает, как инициализироваться.
        return cls()  # type: ignore[call-arg]  # у наших отчётов есть дефолтный конструктор

    def available(self) -> List[str]:
        """
        Получить список доступных имён отчётов.

        Returns:
            list[str]: Отсортированный список зарегистрированных ключей.
        """
        return sorted(self._registry.keys())


# -------------------- Singleton-like default registry (lazy) --------------------

# Важно: отложенная инициализация позволяет избежать циклических импортов:
# мы импортируем реализации отчётов только при первом обращении к реестру.
_default_registry: ReportRegistry | None = None


def get_default_registry() -> ReportRegistry:
    """
    Получить singleton-реестр с дефолтными отчётами.

    Поведение:
        - При первом вызове лениво регистрирует встроенные отчёты (average-rating).
        - Дальнейшие вызовы возвращают уже инициализированный реестр.

    Компромисс:
        - Не используем глобальные side-effects при импорте модуля.
          Это упрощает тестирование и ускоряет cold-start CLI.
    """
    global _default_registry
    if _default_registry is None:
        reg = ReportRegistry()
        # Ленивая регистрация, чтобы не создавать цикл импорта:
        from .average_rating import AverageRatingReport  # локальный импорт — только здесь

        reg.register(AverageRatingReport)
        _default_registry = reg
    return _default_registry


def reset_default_registry() -> None:
    """
    Сбросить singleton-реестр (используется в тестах).

    Это даёт возможность изолированно проверять регистрацию/расширение.
    """
    global _default_registry
    _default_registry = None
