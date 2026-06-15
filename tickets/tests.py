from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from accounts.roles import OPERATOR_GROUP
from .models import Category, Notification, Ticket
from .services import auto_assign_ticket, pick_operator


class BaseData(TestCase):
    def setUp(self):
        self.operator_group, _ = Group.objects.get_or_create(name=OPERATOR_GROUP)
        self.cat = Category.objects.create(name="Сеть")

        self.user = User.objects.create_user("student", password="pass12345")
        self.op1 = User.objects.create_user("op1", password="pass12345")
        self.op2 = User.objects.create_user("op2", password="pass12345")
        self.op1.groups.add(self.operator_group)
        self.op2.groups.add(self.operator_group)

    def make_ticket(self, title, description, author=None):
        return Ticket.objects.create(
            author=author or self.user, title=title, description=description, category=self.cat
        )


class AutoAssignmentTests(BaseData):
    def test_pick_least_loaded_operator(self):
        # у op1 уже две открытые заявки, значит выбрать должны op2
        for i in range(2):
            t = self.make_ticket(f"t{i}", "описание")
            t.assignee = self.op1
            t.status = Ticket.Status.IN_PROGRESS
            t.save()
        self.assertEqual(pick_operator(), self.op2)

    def test_auto_assign_sets_assignee_and_status(self):
        ticket = self.make_ticket("Заявка", "описание")
        operator = auto_assign_ticket(ticket)
        ticket.refresh_from_db()
        self.assertIn(operator, [self.op1, self.op2])
        self.assertEqual(ticket.assignee, operator)
        self.assertEqual(ticket.status, Ticket.Status.ASSIGNED)

    def test_assignment_creates_notification(self):
        ticket = self.make_ticket("Заявка", "описание")
        operator = auto_assign_ticket(ticket)
        self.assertTrue(
            Notification.objects.filter(recipient=operator, ticket=ticket).exists()
        )


class StatusNotificationTests(BaseData):
    def test_status_change_notifies_author(self):
        ticket = self.make_ticket("Тема", "описание")
        ticket.status = Ticket.Status.IN_PROGRESS
        ticket.save()
        self.assertTrue(
            Notification.objects.filter(recipient=self.user, ticket=ticket).exists()
        )


class AccessControlTests(BaseData):
    def test_user_cannot_open_foreign_ticket(self):
        other = User.objects.create_user("other", password="pass12345")
        ticket = self.make_ticket("Чужая", "описание", author=other)
        self.client.login(username="student", password="pass12345")
        response = self.client.get(reverse("tickets:ticket_detail", args=[ticket.pk]))
        self.assertRedirects(response, reverse("tickets:ticket_list"))

    def test_operator_can_open_any_ticket(self):
        ticket = self.make_ticket("Заявка", "описание")
        self.client.login(username="op1", password="pass12345")
        response = self.client.get(reverse("tickets:ticket_detail", args=[ticket.pk]))
        self.assertEqual(response.status_code, 200)

    def test_reports_forbidden_for_regular_user(self):
        self.client.login(username="student", password="pass12345")
        response = self.client.get(reverse("tickets:reports"))
        self.assertEqual(response.status_code, 302)

    def test_create_ticket_end_to_end(self):
        self.client.login(username="student", password="pass12345")
        response = self.client.post(
            reverse("tickets:ticket_create"),
            {
                "title": "Не открывается VPN",
                "description": "не подключается vpn",
                "category": self.cat.pk,
                "priority": "normal",
            },
        )
        ticket = Ticket.objects.get(title="Не открывается VPN")
        self.assertRedirects(response, ticket.get_absolute_url())
        self.assertEqual(ticket.category, self.cat)
        self.assertIsNotNone(ticket.assignee)

    def test_category_required(self):
        # без категории форма не должна принимать заявку
        self.client.login(username="student", password="pass12345")
        self.client.post(
            reverse("tickets:ticket_create"),
            {"title": "Без категории", "description": "текст", "priority": "normal"},
        )
        self.assertFalse(Ticket.objects.filter(title="Без категории").exists())
