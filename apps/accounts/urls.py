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
    # Public invitation endpoints (WhiteMatter pattern)
    path("invitation/<str:token>/", views.InvitationInfoView.as_view(), name="invitation-info"),
    path("invitation/<str:token>/accept/", views.AcceptInvitationPublicView.as_view(), name="invitation-accept"),
]
