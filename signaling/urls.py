from django.urls import path
from . import views
urlpatterns = [
    path("rooms/", views.create_room),
    path("rooms/<str:code>/join", views.join_room),
    path("rooms/<str:code>/end", views.end_room),
]
