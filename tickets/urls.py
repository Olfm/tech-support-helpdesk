from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/new/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("reports/", views.reports, name="reports"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/read-all/", views.notifications_read_all, name="notifications_read_all"),
    path("notifications/<int:pk>/", views.notification_read, name="notification_read"),
]
