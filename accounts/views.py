from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SignUpForm


def signup(request):
    # регистрация. После успешной сразу логиним пользователя
    if request.user.is_authenticated:
        return redirect("tickets:dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно. Добро пожаловать!")
            return redirect("tickets:dashboard")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile(request):
    # простая страница профиля
    return render(request, "accounts/profile.html")
