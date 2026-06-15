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
from django.utils import timezone

from accounts.roles import OPERATOR_GROUP
from tickets.models import Category, Ticket, TicketComment

# категории, которые пользователь выбирает при подаче заявки
CATEGORIES = [
    ("Проблемы с интернетом", "Доступ к сети, Wi-Fi, VPN"),
    ("Проблемы с почтой", "Электронная почта, рассылки"),
    ("Доступ к платформам", "Личный кабинет, СДО, пароли"),
    ("Оборудование", "Принтеры, мониторы, периферия"),
    ("Другое", "Прочие обращения"),
]

# демо-заявки: тема, описание, категория
DEMO_TICKETS = [
    ("Не открывается личный кабинет", "Не могу войти в LMS, не принимает пароль.", "Доступ к платформам"),
    ("Пропал интернет в аудитории", "В 312 аудитории не работает wi-fi.", "Проблемы с интернетом"),
    ("Не приходят письма", "На почту не приходят уведомления о расписании.", "Проблемы с почтой"),
    ("Не печатает принтер", "Принтер на кафедре не реагирует на отправку документа.", "Оборудование"),
    ("Вопрос по расписанию", "Где посмотреть актуальное расписание сессии?", "Другое"),
]

# несколько операторов, чтобы заявки решал не один человек (только имена)
OPERATORS = [
    ("operator", "Олег"),
    ("operator_anna", "Анна"),
    ("operator_dmitry", "Дмитрий"),
]

# сценарий по каждой заявке: кто решает, статус и переписка.
# у решённых заявок диалог заканчивается ответом с итогом.
# роль в переписке: operator (отвечает назначенный оператор) или student.
DEMO_FLOW = [
    {
        "title": "Не открывается личный кабинет",
        "operator": "operator",
        "status": "resolved",
        "messages": [
            ("operator", "Здравствуйте! Сбросил вам пароль, на почту придёт ссылка для входа. Попробуйте войти и напишите, если не получится."),
            ("student", "Спасибо, всё заработало!"),
            ("operator", "Рад помочь! Тогда закрываю заявку. Если снова будут проблемы со входом, пишите."),
        ],
    },
    {
        "title": "Пропал интернет в аудитории",
        "operator": "operator_anna",
        "status": "resolved",
        "messages": [
            ("operator", "Здравствуйте! Передала заявку сетевому администратору, проверим точку доступа в 312."),
            ("operator", "Точку доступа в 312 перезагрузили, Wi-Fi снова работает. Заявку закрываю."),
        ],
    },
    {
        "title": "Не приходят письма",
        "operator": "operator_anna",
        "status": "in_progress",
        "messages": [
            ("operator", "Здравствуйте! Разбираюсь с рассылкой уведомлений. Подскажите, пожалуйста, проверяли ли вы папку «Спам»?"),
        ],
    },
    {
        "title": "Не печатает принтер",
        "operator": "operator_dmitry",
        "status": "in_progress",
        "messages": [
            ("operator", "Здравствуйте! Принял заявку в работу, подойду к принтеру на кафедре и проверю подключение."),
        ],
    },
    {
        "title": "Вопрос по расписанию",
        "operator": "operator",
        "status": "resolved",
        "messages": [
            ("operator", "Здравствуйте! Расписание сессии есть в личном кабинете в разделе «Электронный университет», вкладка «Расписание». Оно же дублируется на сайте в разделе «Студенту»."),
        ],
    },
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
        for name, description in CATEGORIES:
            Category.objects.get_or_create(name=name, defaults={"description": description})

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

        # операторы поддержки (несколько человек)
        op_pw, gen = self.password_for("SEED_OPERATOR_PASSWORD")
        operators = {}
        for username, first in OPERATORS:
            op, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "email": f"{username}@univer-vitte.ru"},
            )
            if created:
                op.set_password(op_pw)
                op.save()
                if gen:
                    generated.append((username, op_pw))
            # имя без фамилии (поправит и уже созданных операторов при повторном запуске)
            if op.first_name != first or op.last_name:
                op.first_name = first
                op.last_name = ""
                op.save(update_fields=["first_name", "last_name"])
            op.groups.add(group)
            operators[username] = op

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

        # демо-заявки создаю только если их ещё нет (категорию задаю явно)
        if not Ticket.objects.exists():
            for title, description, cat_name in DEMO_TICKETS:
                category = Category.objects.filter(name=cat_name).first()
                Ticket.objects.create(
                    author=student, title=title, description=description, category=category
                )

        # разыгрываю сценарий по каждой заявке: исполнитель, переписка и статус.
        # переписку пересобираю заново, чтобы при повторном запуске всё было согласовано.
        status_map = {
            "assigned": Ticket.Status.ASSIGNED,
            "in_progress": Ticket.Status.IN_PROGRESS,
            "resolved": Ticket.Status.RESOLVED,
        }
        for flow in DEMO_FLOW:
            ticket = Ticket.objects.filter(title=flow["title"]).first()
            op = operators.get(flow["operator"])
            if not ticket or not op:
                continue
            ticket.assignee = op
            ticket.comments.all().delete()
            for role, text in flow["messages"]:
                author = op if role == "operator" else student
                TicketComment.objects.create(ticket=ticket, author=author, body=text)
            ticket.status = status_map[flow["status"]]
            ticket.resolved_at = timezone.now() if flow["status"] == "resolved" else None
            ticket.save(update_fields=["assignee", "status", "resolved_at", "updated_at"])

        self.stdout.write(self.style.SUCCESS("Демоданные загружены."))
        if generated:
            self.stdout.write("Сгенерированные учётные данные (сохраните их):")
            for login, pw in generated:
                self.stdout.write(f"  {login}: {pw}")
        else:
            self.stdout.write("Пароли заданы через переменные окружения SEED_*.")
