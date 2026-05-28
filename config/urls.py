"""Главный список адресов. Отсюда подключаются url'ы всех приложений."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("tickets.urls")),
    path("accounts/", include("accounts.urls")),
    path("faq/", include("faq.urls")),
    path("forum/", include("forum.urls")),
]

# подписи в админке, чтобы было понятнее
admin.site.site_header = "Служба технической поддержки: администрирование"
admin.site.site_title = "Техподдержка"
admin.site.index_title = "Управление сервисом"
