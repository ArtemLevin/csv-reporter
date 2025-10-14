"""
CSV Rating Reporter package initializer.

Назначение:
- Гарантированно экспортирует __version__ (используется тестами и флагом --version).
- Не выполняет побочных эффектов (логирование/CLI не конфигурируется здесь).

Подход:
- Сначала определяем константу-делегат (__version__) с безопасным значением.
- Затем пытаемся переопределить её значением из метаданных установленного дистрибутива.
- Это делает импорт `from csv_reporter import __version__` стабильным как при editable-установке,
  так и при запуске кода напрямую из `src/` до установки.
"""

from __future__ import annotations

# Фолбэк-версия должна соответствовать [project].version из pyproject.toml
__version__ = "1.0.0"  # будет переопределена, если найдём метаданные пакета

try:
    # Python 3.8+: стандартный способ получить версию установленного дистрибутива
    from importlib.metadata import version as _dist_version  # type: ignore

    # Имя дистрибутива берём из pyproject.toml -> [project].name
    __version__ = _dist_version("csv-rating-reporter")
except Exception:
    # Любая проблема (нет метаданных, не установлен в окружение и т.п.) — оставляем фолбэк
    pass

__all__ = ["__version__"]
