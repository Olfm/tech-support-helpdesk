from django.db import models


class FaqItem(models.Model):
    # один вопрос-ответ в разделе FAQ
    question = models.CharField("Вопрос", max_length=255)
    answer = models.TextField("Ответ")
    order = models.PositiveIntegerField("Порядок", default=0)
    is_published = models.BooleanField("Опубликовано", default=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Вопрос-ответ"
        verbose_name_plural = "Вопросы и ответы (FAQ)"
        ordering = ["order", "id"]

    def __str__(self):
        return self.question
