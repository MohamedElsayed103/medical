from django.urls import path

from . import views

urlpatterns = [
    path("", views.health_check, name="health"),
    path("db/", views.db_health, name="health-db"),
    path("redis/", views.redis_health, name="health-redis"),
]
