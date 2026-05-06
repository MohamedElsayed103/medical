"""
DRF authentication class for Keycloak JWT tokens.

Extracts the Bearer token from the Authorization header and delegates
validation to KeycloakOIDCBackend.
"""
from django.contrib.auth import authenticate
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class KeycloakJWTAuthentication(BaseAuthentication):
    """
    DRF authentication class.

    Expects:  Authorization: Bearer <access_token>
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(f"{self.keyword} "):
            return None  # No token — let other backends try

        token = auth_header[len(self.keyword) + 1 :]
        if not token:
            return None

        user = authenticate(request=request, token=token)
        if user is None:
            raise AuthenticationFailed("Invalid or expired token.")
        if not user.is_active:
            raise AuthenticationFailed("User account is deactivated.")

        return (user, token)

    def authenticate_header(self, request):
        return self.keyword
