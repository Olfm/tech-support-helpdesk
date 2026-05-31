from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .roles import OPERATOR_GROUP, is_operator


class RoleHelperTests(TestCase):
    def test_anonymous_is_not_operator(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertFalse(is_operator(AnonymousUser()))

    def test_superuser_is_operator(self):
        admin = User.objects.create_superuser("root", "root@example.com", "pass12345")
        self.assertTrue(is_operator(admin))

    def test_group_membership_grants_operator(self):
        group, _ = Group.objects.get_or_create(name=OPERATOR_GROUP)
        user = User.objects.create_user("op", password="pass12345")
        self.assertFalse(is_operator(user))
        user.groups.add(group)
        self.assertTrue(is_operator(user))


class SignUpFlowTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "newuser",
                "first_name": "Иван",
                "last_name": "Петров",
                "email": "ivan@example.com",
                "password1": "Sl0zhniyParol!",
                "password2": "Sl0zhniyParol!",
            },
        )
        self.assertRedirects(response, reverse("tickets:dashboard"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_duplicate_email_rejected(self):
        User.objects.create_user("a", email="dup@example.com", password="x")
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "b",
                "first_name": "А",
                "last_name": "Б",
                "email": "dup@example.com",
                "password1": "Sl0zhniyParol!",
                "password2": "Sl0zhniyParol!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="b").exists())
