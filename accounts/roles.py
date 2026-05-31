"""
Роли в сервисе.

Ролей две, обе сделаны через обычные группы Django:

- OPERATOR: сотрудник поддержки (оператор). Видит все заявки, назначает их,
  меняет статусы, модерирует форум и FAQ.
- обычный пользователь (студент или сотрудник). Подаёт заявки, смотрит их
  статус, пользуется форумом и FAQ.

Суперпользователя считаю оператором сразу, без проверки группы.
"""

from django.contrib.auth.models import Group

OPERATOR_GROUP = "operator"


def is_operator(user) -> bool:
    # оператор ли это
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=OPERATOR_GROUP).exists()


def ensure_groups() -> Group:
    # создаёт группу операторов, если её ещё нет
    group, _ = Group.objects.get_or_create(name=OPERATOR_GROUP)
    return group
