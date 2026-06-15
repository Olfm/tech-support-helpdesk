"""
Логика распределения заявок: новую заявку система сама отдаёт оператору, у
которого сейчас меньше всего открытых заявок.

Вынесла это из views в отдельный файл, чтобы можно было вызывать и из формы, и из
команды seed, а ещё чтобы удобнее было писать тесты.
"""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import Count, Q

from accounts.roles import OPERATOR_GROUP
from .models import Notification, Ticket


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
