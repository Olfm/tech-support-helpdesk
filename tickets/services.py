"""
Тут вся логика обработки заявок: сама определяю категорию по ключевым словам
и отдаю заявку самому свободному оператору.

Вынесла это из views в отдельный файл, чтобы можно было вызывать и из формы, и из
сигналов, и из команды seed, а ещё чтобы удобнее было писать тесты.
"""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import Count, Q

from accounts.roles import OPERATOR_GROUP
from .models import Category, Notification, Ticket


def classify_ticket(ticket: Ticket) -> Category | None:
    # ищу категорию по совпадению ключевых слов в теме и описании.
    # если ничего не нашлось, беру категорию по умолчанию
    text = f"{ticket.title} {ticket.description}".lower()

    best_category = None
    best_score = 0
    for category in Category.objects.all():
        score = sum(1 for kw in category.keyword_list() if kw and kw in text)
        if score > best_score:
            best_score = score
            best_category = category

    if best_category is not None:
        return best_category
    return Category.objects.filter(is_default=True).first()


def operators_queryset():
    # все операторы, кому можно назначать заявки
    return User.objects.filter(groups__name=OPERATOR_GROUP, is_active=True)


def pick_operator() -> User | None:
    # беру оператора, у которого сейчас меньше всего открытых заявок
    operators = operators_queryset().annotate(
        active_load=Count(
            "assigned_tickets",
            filter=Q(assigned_tickets__status__in=Ticket.OPEN_STATUSES),
        )
    ).order_by("active_load", "id")
    return operators.first()


def assign_ticket(ticket: Ticket, operator: User, notify: bool = True) -> Ticket:
    # назначаю заявку оператору и перевожу в статус "Назначена"
    ticket.assignee = operator
    if ticket.status == Ticket.Status.NEW:
        ticket.status = Ticket.Status.ASSIGNED
    ticket.save(update_fields=["assignee", "status", "updated_at"])

    if notify:
        Notification.objects.create(
            recipient=operator,
            ticket=ticket,
            message=f"Вам назначена заявка #{ticket.pk}: {ticket.title}",
        )
    return ticket


def auto_assign_ticket(ticket: Ticket) -> User | None:
    # сам выбираю свободного оператора и назначаю заявку на него
    operator = pick_operator()
    if operator is not None:
        assign_ticket(ticket, operator)
    return operator


def process_new_ticket(ticket: Ticket) -> Ticket:
    # полная обработка новой заявки: определить категорию и назначить оператора
    if ticket.category is None:
        ticket.category = classify_ticket(ticket)
        if ticket.category is not None:
            ticket.save(update_fields=["category", "updated_at"])

    auto_assign_ticket(ticket)
    return ticket
