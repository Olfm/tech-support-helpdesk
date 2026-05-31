from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    # форма регистрации. Имя, фамилию и почту сделала обязательными
    first_name = forms.CharField(label="Имя", max_length=150)
    last_name = forms.CharField(label="Фамилия", max_length=150)
    email = forms.EmailField(label="Электронная почта")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean_email(self):
        # не даём зарегистрировать две учётки на одну почту
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже зарегистрирован.")
        return email
