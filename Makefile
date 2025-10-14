# CSV Rating Reporter — Makefile
# Назначение:
#   Удобные цели для разработки, тестирования, линтинга и сборки без активации venv.
#   Везде используем интерпретатор из виртуального окружения (кроссплатформенно).
#
# Ключевые команды:
#   make venv        — создать .venv
#   make install     — установить проект (dev-зависимости)
#   make format      — автоформатирование (ruff)
#   make lint        — линтинг кода (ruff)
#   make type        — проверка типов (mypy)
#   make test        — pytest (быстро)
#   make cov         — pytest с покрытием
#   make check       — формат + линт + типы + тесты (быстрая проверка перед коммитом)
#   make build       — сборка колеса/сдист (через `python -m build`)
#   make run FILES="a.csv b.csv" [опции] — запуск CLI без установки в систему
#   make clean       — очистить временные артефакты
#
# Комментарии по дизайну:
#   - Не активируем venv через `source`; запускаем инструменты через $(VENVPY) — надёжнее в CI/Windows.
#   - Цели идемпотентны: повторный `make install` безопасен.
#   - Переменные можно переопределять: `make test PYTHON=python3.11`.

# --------------- Переменные окружения ---------------

PYTHON ?= python3
VENV   ?= .venv

# Определяем путь к python внутри venv (кроссплатформенно)
ifeq ($(OS),Windows_NT)
	VENVPY := $(VENV)/Scripts/python.exe
else
	VENVPY := $(VENV)/bin/python
endif

VENVPIP := $(VENVPY) -m pip

# Параметры запуска CLI (можно переопределить при вызове):
REPORT   ?= average-rating
SORT     ?= avg_rating
LIMIT    ?=
TABLEFMT ?= github
FILES    ?=

# --------------- Метки ---------------
.PHONY: help venv install format lint type test cov check build run clean

# Цель по умолчанию
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Common targets:"
	@echo "  venv      - create virtual env in $(VENV)"
	@echo "  install   - install project with dev extras"
	@echo "  format    - ruff format"
	@echo "  lint      - ruff check"
	@echo "  type      - mypy type checking"
	@echo "  test      - run pytest quickly"
	@echo "  cov       - run pytest with coverage"
	@echo "  check     - format + lint + type + test"
	@echo "  build     - build wheel/sdist (ensures 'build' is installed)"
	@echo "  run       - run CLI; pass FILES=\"a.csv b.csv\" and optional SORT/LIMIT/TABLEFMT/REPORT"
	@echo "  clean     - remove caches/build artifacts"

# --------------- Окружение и установка ---------------

# Создать виртуальное окружение
venv:
	@$(PYTHON) -m venv $(VENV)
	@echo "Created venv at $(VENV)"
	@$(VENVPIP) --version >/dev/null

# Установка проекта + dev-зависимостей
install: venv
	@$(VENVPIP) install -U pip
	@$(VENVPIP) install -e ".[dev]"
	@echo "Installed project and dev dependencies into $(VENV)"

# --------------- Качество кода ---------------

# Автоформатирование (ruff-format)
format: venv
	@$(VENVPY) -m ruff format .

# Линтинг (ruff-check)
lint: venv
	@$(VENVPY) -m ruff check .

# Проверка типов (mypy)
type: venv
	@$(VENVPY) -m mypy src

# --------------- Тесты ---------------

# Быстрые тесты
test: venv
	@$(VENVPY) -m pytest -q

# Покрытие (порог задан в pyproject)
cov: venv
	@$(VENVPY) -m pytest --cov=csv_reporter --cov-report=term-missing

# Полный быстрый прогон качества
check: format lint type test

# --------------- Сборка ---------------

# Сборка колеса/сдист (локально)
build: venv
	@$(VENVPIP) install -U build
	@$(VENVPY) -m build

# --------------- Запуск CLI (без установки в PATH) ---------------

# Запуск напрямую через модуль, избегая зависимости от console_scripts.
# Пример:
#   make run FILES="tests/fixtures/sample_ok.csv" SORT=brand LIMIT=10
run: venv
	@if [ -z "$(FILES)" ]; then \
		echo "Error: please pass FILES=\"path1.csv path2.csv\""; exit 1; \
	fi
	@$(VENVPY) -m csv_reporter.cli --files $(FILES) --report $(REPORT) --sort $(SORT) $(if $(LIMIT),--limit $(LIMIT),) --tablefmt $(TABLEFMT)

# --------------- Уборка ---------------

clean:
	@rm -rf \
	  .pytest_cache \
	  .mypy_cache \
	  .ruff_cache \
	  .coverage \
	  dist build \
	  src/*.egg-info \
	  src/*/*.egg-info \
	  *.pyc __pycache__ **/__pycache__
	@echo "Cleaned build and cache artifacts"
