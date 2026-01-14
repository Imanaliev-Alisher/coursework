# Makefile для упрощения команд

.PHONY: help build up down restart logs shell test migrate makemigrations collectstatic superuser populate clean

help:
	@echo "Доступные команды:"
	@echo "  make build         - Собрать Docker контейнеры"
	@echo "  make up            - Запустить проект"
	@echo "  make down          - Остановить проект"
	@echo "  make restart       - Перезапустить проект"
	@echo "  make logs          - Показать логи"
	@echo "  make shell         - Django shell"
	@echo "  make test          - Запустить тесты"
	@echo "  make migrate       - Применить миграции"
	@echo "  make makemigrations- Создать миграции"
	@echo "  make collectstatic - Собрать статические файлы"
	@echo "  make superuser     - Создать суперпользователя"
	@echo "  make populate      - Заполнить тестовыми данными"
	@echo "  make clean         - Очистить временные файлы"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

shell:
	docker compose exec django python manage.py shell

test:
	docker compose exec django pytest apps/users/tests.py apps/buildings/tests.py apps/groups/tests.py apps/studies/tests.py -v

test-cov:
	docker compose exec django pytest apps/users/tests.py apps/buildings/tests.py apps/groups/tests.py apps/studies/tests.py --cov=apps --cov-report=html

migrate:
	docker compose exec django python manage.py migrate

makemigrations:
	docker compose exec django python manage.py makemigrations

collectstatic:
	docker compose exec django python manage.py collectstatic --noinput

superuser:
	docker compose exec django python manage.py createsuperuser

populate:
	docker compose exec django python manage.py populate_db

check:
	docker compose exec django python manage.py check

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
