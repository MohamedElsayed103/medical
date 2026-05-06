"""
Keycloak OIDC authentication backend.

Validates JWT access tokens issued by Keycloak, maps ``sub`` claim
to a local User record, and auto-provisions new users on first login.
"""
import structlog
from django.conf import settings
from django.core.cache import cache

import jwt
import requests

from .models import User

logger = structlog.get_logger(__name__)

JWKS_CACHE_KEY = "keycloak_jwks"
JWKS_CACHE_TTL = 3600  # 1 hour


class KeycloakOIDCBackend:
    """
    Django authentication backend that validates Keycloak JWT tokens.

    Flow:
        1. Fetch JWKS public keys (cached in Redis).
        2. Decode and verify the access token.
        3. Map ``sub`` → User.keycloak_id.
        4. Auto-provision if the user doesn't exist locally.
    """

    def authenticate(self, request, token: str = None, **kwargs):
        if token is None:
            return None

        payload = self._decode_token(token)
        if payload is None:
            return None

        keycloak_id = payload.get("sub")
        if not keycloak_id:
            return None

        user = self._get_or_create_user(keycloak_id, payload)
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    # ── Internal helpers ──

    def _decode_token(self, token: str) -> dict | None:
        """Decode JWT using Keycloak's public keys."""
        try:
            jwks = self._get_jwks()
            public_keys = {}
            for key_data in jwks.get("keys", []):
                kid = key_data.get("kid")
                public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if kid not in public_keys:
                logger.warning("keycloak_kid_not_found", kid=kid)
                return None

            payload = jwt.decode(
                token,
                key=public_keys[kid],
                algorithms=["RS256"],
                audience=settings.OIDC_RP_CLIENT_ID,
                issuer=f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}",
            )
            return payload

        except jwt.ExpiredSignatureError:
            logger.info("keycloak_token_expired")
        except jwt.InvalidTokenError as exc:
            logger.warning("keycloak_invalid_token", error=str(exc))
        return None

    def _get_jwks(self) -> dict:
        """Fetch JWKS from Keycloak, with Redis caching."""
        cached = cache.get(JWKS_CACHE_KEY)
        if cached:
            return cached

        response = requests.get(settings.OIDC_OP_JWKS_ENDPOINT, timeout=10)
        response.raise_for_status()
        jwks = response.json()
        cache.set(JWKS_CACHE_KEY, jwks, JWKS_CACHE_TTL)
        return jwks

    def _get_or_create_user(self, keycloak_id: str, payload: dict) -> User:
        """Lookup user by keycloak_id or auto-provision from token claims."""
        try:
            return User.objects.get(keycloak_id=keycloak_id)
        except User.DoesNotExist:
            pass

        email = payload.get("email", "")
        if not email:
            logger.error("keycloak_no_email_claim", sub=keycloak_id)
            return None

        # Check if user exists by email (e.g., created via admin before first OIDC login)
        user = User.objects.filter(email=email).first()
        if user:
            user.keycloak_id = keycloak_id
            user.save(update_fields=["keycloak_id"])
            logger.info("keycloak_user_linked", user_id=str(user.id), keycloak_id=keycloak_id)
            return user

        # Auto-provision
        user = User.objects.create_user(
            email=email,
            first_name=payload.get("given_name", ""),
            last_name=payload.get("family_name", ""),
            keycloak_id=keycloak_id,
        )
        logger.info("keycloak_user_provisioned", user_id=str(user.id), email=email)
        return user
