#!/usr/bin/env python
"""Через этот файл запускаются команды Django: runserver, migrate и другие."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # сюда попадаем, если Django не установлен или забыли включить venv
        raise ImportError(
            "Не получилось импортировать Django. Проверьте, что он установлен "
            "и что виртуальное окружение активно."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
