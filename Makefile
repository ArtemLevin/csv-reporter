# CSV Rating Reporter — Makefile (robust demo)
# Назначение:
#   Удобные цели для разработки, тестирования, линтинга, сборки и демонстрации работы CLI.
#   Все инструменты запускаются через Python из виртуального окружения (без ручного source).
#
# Ключевые команды:
#   make install   — создать .venv и установить проект с dev-зависимостями (editable)
#   make test      — pytest (зависит от install)
#   make cov       — pytest с покрытием (зависит от install)
#   make run ...   — запуск CLI (FILES="a.csv b.csv" и др. параметры)
#   make demo      — генерация примеров CSV и сохранение вывода/ошибок в examples/
#   make check     — format + lint + type + test
#   make build     — сборка wheel/sdist
#   make clean     — очистка артефактов

# --------------- Переменные окружения ---------------

PYTHON ?= python3
VENV   ?= .venv

ifeq ($(OS),Windows_NT)
	VENVPY := $(VENV)/Scripts/python.exe
else
	VENVPY := $(VENV)/bin/python
endif

VENVPIP := $(VENVPY) -m pip

# Параметры CLI (можно переопределять при вызове make)
REPORT   ?= average-rating
SORT     ?= avg_rating
LIMIT    ?=
TABLEFMT ?= github
FILES    ?=

# Директория с примерами
EXAMPLES_DIR := examples

# --------------- Метки ---------------
.PHONY: help venv install format lint type test cov check build run demo clean

# Цель по умолчанию
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Common targets:"
	@echo "  install  - create venv and install project with dev extras"
	@echo "  test     - run pytest (depends on install)"
	@echo "  cov      - run pytest with coverage (depends on install)"
	@echo "  run      - run CLI; pass FILES=\"a.csv b.csv\" and optional SORT/LIMIT/TABLEFMT/REPORT"
	@echo "  demo     - generate demo CSVs and save output to $(EXAMPLES_DIR)/demo_output.txt (stderr -> demo_error.txt)"
	@echo "  check    - format + lint + type + test"
	@echo "  build    - build wheel/sdist"
	@echo "  clean    - remove caches/build artifacts"

# --------------- Окружение и установка ---------------

venv:
	@$(PYTHON) -m venv $(VENV)
	@echo "Created venv at $(VENV)"
	@$(VENVPIP) --version >/dev/null

install: venv
	@$(VENVPIP) install -U pip
	@$(VENVPIP) install -e ".[dev]"
	@echo "Installed project and dev dependencies into $(VENV)"

# --------------- Качество кода ---------------

format: install
	@$(VENVPY) -m ruff format .

lint: install
	@$(VENVPY) -m ruff check .

type: install
	@$(VENVPY) -m mypy src

# --------------- Тесты ---------------

test: install
	@$(VENVPY) -m pytest -q

cov: install
	@$(VENVPY) -m pytest --cov=csv_reporter --cov-report=term-missing

check: format lint type test

# --------------- Сборка ---------------

build: install
	@$(VENVPIP) install -U build
	@$(VENVPY) -m build

# --------------- Запуск CLI ---------------

run: install
	@if [ -z "$(FILES)" ]; then \
		echo "Error: please pass FILES=\"path1.csv path2.csv\""; exit 1; \
	fi
	@$(VENVPY) -m csv_reporter.cli --files $(FILES) --report $(REPORT) --sort $(SORT) $(if $(LIMIT),--limit $(LIMIT),) --tablefmt $(TABLEFMT)

# --------------- Демонстрация (генерация CSV + устойчивый вывод) ---------------

$(EXAMPLES_DIR)/products_1.csv:
	@mkdir -p $(EXAMPLES_DIR)
	@printf 'name,brand,price,rating\n' > $@
	@printf 'iPhone 15,Apple,999,4.8\n' >> $@
	@printf 'Pixel 9,Google,799,4.5\n' >> $@
	@printf 'Galaxy S24,Samsung,899,4.6\n' >> $@

$(EXAMPLES_DIR)/products_2.csv:
	@mkdir -p $(EXAMPLES_DIR)
	@printf 'name,brand,price,rating\n' > $@
	@printf 'MacBook Air,Apple,1299,4.7\n' >> $@
	@printf 'ThinkPad X1,Lenovo,1499,4.4\n' >> $@
	@printf 'Some device,Unknown,199,\n' >> $@

demo: install $(EXAMPLES_DIR)/products_1.csv $(EXAMPLES_DIR)/products_2.csv
	@mkdir -p $(EXAMPLES_DIR)
	@set -e; \
	OUT="$(EXAMPLES_DIR)/demo_output.txt"; \
	ERR="$(EXAMPLES_DIR)/demo_error.txt"; \
	: > "$$OUT"; : > "$$ERR"; \
	$(VENVPY) -m csv_reporter.cli \
		--files $(EXAMPLES_DIR)/products_1.csv $(EXAMPLES_DIR)/products_2.csv \
		--report average-rating --sort avg_rating --tablefmt github \
		> "$$OUT" 2> "$$ERR" || true; \
	if [ -s "$$OUT" ]; then \
		echo "Wrote $$OUT"; \
	else \
		echo "Demo produced no table. Inspecting errors:"; \
		if [ -s "$$ERR" ]; then cat "$$ERR"; else echo "(no stderr output)"; fi; \
		exit 1; \
	fi

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
