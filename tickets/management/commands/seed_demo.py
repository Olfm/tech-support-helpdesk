"""
Команда, которая наполняет базу демо-данными, чтобы было что показать.

Создаёт группу операторов, категории с ключевыми словами, пару пользователей и
несколько заявок (их прогоняю через автоклассификацию и автораспределение).
Пароли беру из переменных окружения, а если их нет - генерирую и печатаю один
раз. В коде пароли не храню.

    python manage.py seed_demo
"""

from __future__ import annotations

import os
import secrets

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from accounts.roles import OPERATOR_GROUP
from tickets.models import Category, Ticket
from tickets.services import process_new_ticket

# ключевые слова даю основами (без окончаний), чтобы ловить разные формы:
# "почт" подойдёт и к "почта", и к "почту", и к "почтой"
CATEGORIES = [
    ("Проблемы с интернетом", "интернет, сеть, vpn, wi-fi, подключ", False),
    ("Проблемы с почтой", "почт, email, письм, рассылк, ящик", False),
    ("Доступ к платформам", "lms, moodle, кабинет, пароль, вход, доступ", False),
    ("Оборудование", "принтер, монитор, клавиатур, мыш, периферия, печат", False),
    ("Другое", "", True),
]

DEMO_TICKETS = [
    ("Не открывается личный кабинет", "Не могу войти в LMS, не принимает пароль."),
    ("Пропал интернет в аудитории", "В 312 аудитории не работает wi-fi."),
    ("Не приходят письма", "На почту не приходят уведомления о расписании."),
    ("Не печатает принтер", "Принтер на кафедре не реагирует на отправку документа."),
    ("Вопрос по расписанию", "Где посмотреть актуальное расписание сессии?"),
]


class Command(BaseCommand):
    help = "Наполняет базу демонстрационными данными для проверки сервиса."

    def password_for(self, env_name: str) -> tuple[str, bool]:
        # пароль из окружения, либо сгенерированный (второе значение - флаг "сгенерили")
        value = os.environ.get(env_name)
        if value:
            return value, False
        return secrets.token_urlsafe(9), True

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=OPERATOR_GROUP)

        # категории
        for name, keywords, is_default in CATEGORIES:
            Category.objects.get_or_create(
                name=name, defaults={"keywords": keywords, "is_default": is_default}
            )

        generated = []

        # суперпользователь (админка)
        admin_pw, gen = self.password_for("SEED_ADMIN_PASSWORD")
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "email": "admin@univer-vitte.ru"},
        )
        if created:
            admin.set_password(admin_pw)
            admin.save()
            if gen:
                generated.append(("admin (суперпользователь)", admin_pw))

        # оператор поддержки
        op_pw, gen = self.password_for("SEED_OPERATOR_PASSWORD")
        operator, created = User.objects.get_or_create(
            username="operator",
            defaults={"first_name": "Олег", "last_name": "Поддержкин", "email": "operator@univer-vitte.ru"},
        )
        if created:
            operator.set_password(op_pw)
            operator.save()
            if gen:
                generated.append(("operator", op_pw))
        operator.groups.add(group)

        # обычный пользователь (студент)
        user_pw, gen = self.password_for("SEED_USER_PASSWORD")
        student, created = User.objects.get_or_create(
            username="student",
            defaults={"first_name": "Мария", "last_name": "Студентова", "email": "student@univer-vitte.ru"},
        )
        if created:
            student.set_password(user_pw)
            student.save()
            if gen:
                generated.append(("student", user_pw))

        # демо-заявки создаю только если их ещё нет
        if not Ticket.objects.exists():
            for title, description in DEMO_TICKETS:
                ticket = Ticket.objects.create(
                    author=student, title=title, description=description
                )
                process_new_ticket(ticket)

        self.stdout.write(self.style.SUCCESS("Демоданные загружены."))
        if generated:
            self.stdout.write("Сгенерированные учётные данные (сохраните их):")
            for login, pw in generated:
                self.stdout.write(f"  {login}: {pw}")
        else:
            self.stdout.write("Пароли заданы через переменные окружения SEED_*.")
