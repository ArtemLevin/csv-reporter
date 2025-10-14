# Ключевые команды:
#   make venv        — создать .venv
#   make install     — установить проект (dev-зависимости)
#   make format      — автоформатирование (ruff)
#   make lint        — линтинг кода (ruff)
#   make type        — проверка типов (mypy)
#   make test        — pytest (быстро)  ⟵ теперь зависит от install
#   make cov         — pytest с покрытием ⟵ теперь зависит от install
#   make check       — format + lint + type + test
#   make build       — сборка wheel/sdist (через `python -m build`)
#   make run FILES="a.csv b.csv" [SORT=.. LIMIT=.. TABLEFMT=.. REPORT=..] — запуск CLI
#   make clean       — очистить временные артефакты
#
# Примечания:
#   - Не активируем venv через `source`; вызываем $(VENVPY) напрямую — стабильно и для CI, и для Windows.
#   - Цели идемпотентны: повторный `make install` безопасен.
#   - Переменные можно переопределять при вызове: `make test PYTHON=python3.11`.

# --------------- Переменные окружения ---------------

PYTHON ?= python3
VENV   ?= .venv

# Внутренний python в venv (кроссплатформенно)
ifeq ($(OS),Windows_NT)
	VENVPY := $(VENV)/Scripts/python.exe
else
	VENVPY := $(VENV)/bin/python
endif

VENVPIP := $(VENVPY) -m pip

# Параметры CLI (можно переопределить при вызове make)
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
	@echo "  test      - run pytest (depends on install)"
	@echo "  cov       - run pytest with coverage (depends on install)"
	@echo "  check     - format + lint + type + test"
	@echo "  build     - build wheel/sdist"
	@echo "  run       - run CLI; pass FILES=\"a.csv b.csv\" and optional SORT/LIMIT/TABLEFMT/REPORT"
	@echo "  clean     - remove caches/build artifacts"

# --------------- Окружение и установка ---------------

# Создать виртуальное окружение
venv:
	@$(PYTHON) -m venv $(VENV)
	@echo "Created venv at $(VENV)"
	@$(VENVPIP) --version >/dev/null

# Установка проекта + dev-зависимостей (editable)
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

# Быстрые тесты — теперь зависят от install, чтобы гарантировать импорт пакета
test: install
	@$(VENVPY) -m pytest -q

# Покрытие — также зависят от install
cov: install
	@$(VENVPY) -m pytest --cov=csv_reporter --cov-report=term-missing

# Полный быстрый прогон качества
check: format lint type test

# --------------- Сборка ---------------

# Сборка wheel/sdist
build: install
	@$(VENVPIP) install -U build
	@$(VENVPY) -m build

# --------------- Запуск CLI (без установки в PATH) ---------------

# Запуск через модуль — поддерживает все аргументы CLI, включая --tablefmt.
# Пример:
#   make run FILES="tests/fixtures/sample_ok.csv" SORT=brand LIMIT=10 TABLEFMT=simple
run: install
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
	  **/__pycache__ \
	  *.pyc __pycache__
	@echo "Cleaned build and cache artifacts"
