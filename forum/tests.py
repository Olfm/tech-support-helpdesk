from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Post, Topic


class ForumTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", password="pass12345")

    def test_create_topic_creates_first_post(self):
        self.client.login(username="u", password="pass12345")
        response = self.client.post(
            reverse("forum:topic_create"),
            {"title": "Как настроить VPN?", "body": "Подскажите по настройке."},
        )
        topic = Topic.objects.get(title="Как настроить VPN?")
        self.assertRedirects(response, topic.get_absolute_url())
        self.assertEqual(topic.posts.count(), 1)

    def test_anonymous_cannot_create_topic(self):
        response = self.client.get(reverse("forum:topic_create"))
        self.assertEqual(response.status_code, 302)

    def test_reply_added_to_topic(self):
        topic = Topic.objects.create(title="Тема", author=self.user)
        self.client.login(username="u", password="pass12345")
        self.client.post(reverse("forum:topic_detail", args=[topic.pk]), {"body": "Ответ"})
        self.assertEqual(Post.objects.filter(topic=topic).count(), 1)
