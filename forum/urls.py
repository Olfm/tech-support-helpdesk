from django.urls import path

from . import views

app_name = "forum"

urlpatterns = [
    path("", views.topic_list, name="topic_list"),
    path("new/", views.topic_create, name="topic_create"),
    path("<int:pk>/", views.topic_detail, name="topic_detail"),
    path("<int:pk>/toggle-close/", views.topic_toggle_close, name="topic_toggle_close"),
]
