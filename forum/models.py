from django.conf import settings
from django.db import models
from django.urls import reverse


class Topic(models.Model):
    # тема на форуме
    title = models.CharField("Заголовок", max_length=200)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topics",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    is_closed = models.BooleanField("Закрыта", default=False)

    class Meta:
        verbose_name = "Тема форума"
        verbose_name_plural = "Темы форума"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("forum:topic_detail", args=[self.pk])


class Post(models.Model):
    # сообщение внутри темы
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="posts", verbose_name="Тема"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор"
    )
    body = models.TextField("Сообщение")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение форума"
        verbose_name_plural = "Сообщения форума"
        ordering = ["created_at"]

    def __str__(self):
        return f"Сообщение в теме «{self.topic.title}»"
