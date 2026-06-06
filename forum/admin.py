from django.contrib import admin

from .models import Post, Topic


class PostInline(admin.TabularInline):
    model = Post
    extra = 0
    readonly_fields = ["author", "created_at"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "is_closed", "created_at"]
    list_filter = ["is_closed"]
    search_fields = ["title"]
    inlines = [PostInline]
