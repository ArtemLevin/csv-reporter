"""
Presentation helpers (tabular output) for CSV Rating Reporter.

Назначение:
- Преобразует доменные DTO в человекочитаемую таблицу для stdout.
- Ответственность только за форматирование; никакой бизнес-логики/IO чтения.

Публичное API:
- class TablePresenter:
    - render_brand_stats(rows, sort_by="avg_rating", descending=True, limit=None, tablefmt="github") -> str

Политики:
- Используем `tabulate` для вывода таблицы (минимальная зависимость по SRS).
- Округление среднего рейтинга до 2 знаков — компромисс читаемости.
- Важно: передаём `disable_numparse=True`, чтобы tabulate НЕ превращал строки `"4.00"` обратно в числа `4`,
  иначе теряются нули после запятой (это ломало тест, ожидающий «4.00»).
"""

from __future__ import annotations

from typing import Iterable, List, Literal, Optional, Sequence, Tuple

from tabulate import tabulate

from .model import BrandStats

# Разрешённые поля сортировки (явно фиксируем контракт)
SortField = Literal["brand", "avg_rating", "items"]


class TablePresenter:
    """
    Форматирование отчётов в виде таблиц.

    Комментарии по SOLID:
    - SRP: только форматирование данных. Сортировку держим здесь,
      т.к. это аспект представления (какой порядок удобнее пользователю).
    - OCP: при добавлении новых DTO/отчётов можно расширить класс новыми методами,
      не меняя существующие.
    """

    def render_brand_stats(
        self,
        rows: Sequence[BrandStats],
        *,
        sort_by: SortField = "avg_rating",
        descending: bool = True,
        limit: Optional[int] = None,
        tablefmt: str = "github",
    ) -> str:
        """
        Сформировать текст таблицы по списку BrandStats.

        Args:
            rows: Входные агрегированные данные.
            sort_by: Поле сортировки: "brand" | "avg_rating" | "items".
            descending: True для убывания (по умолчанию для рейтинга это логично).
            limit: Необязательное ограничение количества строк в выводе.
            tablefmt: Формат tabulate (по умолчанию "github" для хорошей читаемости).
        Returns:
            str: Готовая строка таблицы для печати в stdout.
        """
        # --- Сортировка как часть представления ---
        key_func = self._get_sort_key(sort_by)
        # Не модифицируем исходную последовательность — создаём отсортированный список
        ordered: List[BrandStats] = sorted(rows, key=key_func, reverse=descending)

        if limit is not None and limit >= 0:
            ordered = ordered[:limit]

        # --- Подготовка табличных данных ---
        headers = ["brand", "avg_rating", "items"]
        table: List[Tuple[str, str, int]] = []

        for r in ordered:
            # Округляем средний рейтинг до 2 знаков для компактности и ПРИНУДИТЕЛЬНО
            # сохраняем строкой, чтобы не потерять нули при табулировании.
            avg_display = f"{r.avg_rating:.2f}"
            table.append((r.brand, avg_display, r.items))

        # disable_numparse=True — критично для сохранения строкового представления "4.00"
        return tabulate(
            table,
            headers=headers,
            tablefmt=tablefmt,
            disable_numparse=True,  # не пытайся распарсить "4.00" обратно в число 4
        )

    # ----------------------- internal helpers -----------------------

    def _get_sort_key(self, sort_by: SortField):
        """
        Вернуть функцию-ключ сортировки по выбранному полю.

        Почему не лямбда в месте вызова:
        - Так проще покрывать тестами и валидировать корректность выбора поля.
        """
        if sort_by == "brand":
            return lambda r: r.brand  # сортируем по строке бренда (a..z)
        if sort_by == "avg_rating":
            return lambda r: r.avg_rating  # по среднему рейтингу
        if sort_by == "items":
            return lambda r: r.items  # по количеству элементов
        # Теоретически сюда не попадём, т.к. тип Literal ограничивает значения,
        # но оставим защиту на случай изменения сигнатуры.
        raise ValueError(f"Unsupported sort field: {sort_by!r}")
