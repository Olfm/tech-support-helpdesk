from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    # категория заявки, которую выбирает пользователь при подаче
    name = models.CharField("Название", max_length=100, unique=True)
    description = models.CharField("Описание", max_length=255, blank=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ticket(models.Model):
    # заявка в поддержку

    class Status(models.TextChoices):
        NEW = "new", "Новая"
        ASSIGNED = "assigned", "Назначена"
        IN_PROGRESS = "in_progress", "В работе"
        RESOLVED = "resolved", "Решена"
        CLOSED = "closed", "Закрыта"

    class Priority(models.TextChoices):
        LOW = "low", "Низкий"
        NORMAL = "normal", "Обычный"
        HIGH = "high", "Высокий"
        URGENT = "urgent", "Срочный"

    # статусы, при которых заявка считается ещё открытой
    OPEN_STATUSES = [Status.NEW, Status.ASSIGNED, Status.IN_PROGRESS]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name="Заявитель",
    )
    title = models.CharField("Тема", max_length=150)
    description = models.TextField("Описание проблемы")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
        verbose_name="Категория",
    )
    priority = models.CharField(
        "Приоритет", max_length=10, choices=Priority.choices, default=Priority.NORMAL
    )
    status = models.CharField(
        "Статус", max_length=15, choices=Status.choices, default=Status.NEW
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name="Исполнитель",
    )
    contact_email = models.EmailField("Контактная почта", blank=True)
    contact_phone = models.CharField("Контактный телефон", max_length=20, blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)
    resolved_at = models.DateTimeField("Решена", null=True, blank=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["assignee"]),
        ]

    def __str__(self):
        return f"#{self.pk} {self.title}"

    def get_absolute_url(self):
        return reverse("tickets:ticket_detail", args=[self.pk])

    @property
    def is_open(self) -> bool:
        return self.status in self.OPEN_STATUSES

    def mark_resolved(self):
        # помечаю заявку решённой и ставлю время решения
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])

    def resolution_hours(self):
        # сколько часов ушло на решение (None, если ещё не решена)
        if self.resolved_at:
            return round((self.resolved_at - self.created_at).total_seconds() / 3600, 1)
        return None


class TicketComment(models.Model):
    # переписка по заявке: сообщения между студентом и оператором
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="comments", verbose_name="Заявка"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор"
    )
    body = models.TextField("Сообщение")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий к заявке"
        verbose_name_plural = "Комментарии к заявкам"
        ordering = ["created_at"]

    def __str__(self):
        return f"Комментарий к заявке #{self.ticket_id}"


class Notification(models.Model):
    # уведомление пользователю: назначили заявку, сменился статус, пришёл ответ
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Получатель",
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name="Заявка",
    )
    message = models.CharField("Текст", max_length=255)
    is_read = models.BooleanField("Прочитано", default=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
