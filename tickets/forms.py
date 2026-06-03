from django import forms

from .models import Ticket, TicketComment
from .services import operators_queryset


class TicketForm(forms.ModelForm):
    # форма, через которую пользователь подаёт заявку
    class Meta:
        model = Ticket
        fields = ["title", "description", "category", "priority", "contact_email", "contact_phone"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }
        help_texts = {
            "category": "Можно не выбирать, система определит категорию сама.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # категорию и контакты делаю необязательными
        self.fields["category"].required = False
        self.fields["contact_email"].required = False
        self.fields["contact_phone"].required = False


class TicketCommentForm(forms.ModelForm):
    # форма ответа в переписке по заявке
    class Meta:
        model = TicketComment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Ваш ответ..."})}
        labels = {"body": ""}


class TicketManageForm(forms.ModelForm):
    # этой формой оператор управляет заявкой
    class Meta:
        model = Ticket
        fields = ["status", "assignee", "category", "priority"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # в исполнителях показываю только операторов
        self.fields["assignee"].queryset = operators_queryset()
        self.fields["assignee"].required = False
