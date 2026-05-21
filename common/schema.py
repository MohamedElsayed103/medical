"""
OpenAPI schema extensions for drf-spectacular.

Registers the KeycloakJWTAuthentication class so Swagger shows the
"Authorize" button with Bearer token input.
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class KeycloakJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.accounts.authentication.KeycloakJWTAuthentication"
    name = "BearerAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT from SimpleJWT (dev) or Keycloak OIDC (prod). Use the /api/v1/auth/login/ endpoint to obtain tokens.",
        }
