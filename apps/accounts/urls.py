from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("verify-pin/", views.VerifyPinView.as_view(), name="verify-pin"),
    path("api-keys/", views.ApiKeyView.as_view(), name="api-keys"),
]
