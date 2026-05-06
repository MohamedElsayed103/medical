from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("me/", views.MeView.as_view(), name="me"),
    path("verify-pin/", views.VerifyPinView.as_view(), name="verify-pin"),
    path("api-keys/", views.ApiKeyView.as_view(), name="api-keys"),
]
