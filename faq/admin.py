from django.contrib import admin

from .models import FaqItem


@admin.register(FaqItem)
class FaqItemAdmin(admin.ModelAdmin):
    list_display = ["question", "order", "is_published", "updated_at"]
    list_editable = ["order", "is_published"]
    search_fields = ["question", "answer"]
