from django.contrib import admin

from .models import Category, Notification, Ticket, TicketComment


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ["author", "created_at"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "author", "category", "priority", "status", "assignee", "created_at"]
    list_filter = ["status", "priority", "category"]
    search_fields = ["title", "description", "author__username"]
    autocomplete_fields = ["author", "assignee", "category"]
    readonly_fields = ["created_at", "updated_at", "resolved_at"]
    inlines = [TicketCommentInline]
    date_hierarchy = "created_at"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "message", "is_read", "created_at"]
    list_filter = ["is_read"]
