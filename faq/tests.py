from django.test import TestCase
from django.urls import reverse

from .models import FaqItem


class FaqTests(TestCase):
    def test_only_published_items_shown(self):
        FaqItem.objects.create(question="Как сбросить пароль?", answer="Через кабинет.")
        FaqItem.objects.create(question="Черновик", answer="...", is_published=False)
        response = self.client.get(reverse("faq:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Как сбросить пароль?")
        self.assertNotContains(response, "Черновик")

    def test_seed_migration_populated_faq(self):
        # Миграция 0002 наполняет раздел типовыми вопросами студента.
        self.assertTrue(
            FaqItem.objects.filter(question="Как войти в личный кабинет?").exists()
        )
        self.assertGreaterEqual(FaqItem.objects.count(), 11)
