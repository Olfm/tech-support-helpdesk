from django.shortcuts import render

from .models import FaqItem


def faq_list(request):
    # показываю только опубликованные вопросы, открыто всем
    items = FaqItem.objects.filter(is_published=True)
    return render(request, "faq/faq_list.html", {"items": items})
