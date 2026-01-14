import pytest
from django.conf import settings
import os
import django
import sys

# Настройки для pytest-django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

pytest_plugins = ['pytest_django']


def pytest_configure(config):
    """Конфигурация pytest"""
    # Добавляем корневую директорию в PYTHONPATH
    sys.path.insert(0, os.path.dirname(__file__))


def pytest_collection_modifyitems(config, items):
    """Модификация собранных тестов"""
    # Можно добавить автоматическую маркировку тестов
    pass
