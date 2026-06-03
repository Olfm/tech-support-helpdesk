from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tickets"
    verbose_name = "Заявки технической поддержки"

    def ready(self):
        # подключаю сигналы при старте приложения
        from . import signals  # noqa: F401
