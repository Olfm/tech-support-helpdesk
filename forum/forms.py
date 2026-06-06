from django import forms

from .models import Post, Topic


class TopicForm(forms.ModelForm):
    # создание темы вместе с первым сообщением
    body = forms.CharField(label="Сообщение", widget=forms.Textarea(attrs={"rows": 5}))

    class Meta:
        model = Topic
        fields = ["title"]


class PostForm(forms.ModelForm):
    # ответ в теме
    class Meta:
        model = Post
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Ваш ответ..."})}
        labels = {"body": ""}
