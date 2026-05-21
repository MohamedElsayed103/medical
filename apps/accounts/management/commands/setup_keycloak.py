"""
Management command to configure Keycloak realm for the Healthcare SaaS platform.

Creates the ``healthcare-saas`` realm, ``web-app`` client, and
``service-account`` client via the Keycloak Admin REST API.

Usage:
    python manage.py setup_keycloak
    python manage.py setup_keycloak --keycloak-url http://keycloak:8080 --admin-password secret
"""
import requests
import structlog
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Configure Keycloak realm, clients, and scopes for the Healthcare SaaS platform."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keycloak-url",
            default=getattr(settings, "KEYCLOAK_URL", "http://localhost:8080"),
            help="Keycloak base URL (default from KEYCLOAK_URL setting)",
        )
        parser.add_argument(
            "--admin-user",
            default="admin",
            help="Keycloak admin username (default: admin)",
        )
        parser.add_argument(
            "--admin-password",
            default="admin",
            help="Keycloak admin password (default: admin)",
        )
        parser.add_argument(
            "--realm",
            default=getattr(settings, "KEYCLOAK_REALM", "healthcare-saas"),
            help="Realm to create (default from KEYCLOAK_REALM setting)",
        )
        parser.add_argument(
            "--frontend-url",
            default="http://localhost:3000",
            help="Frontend URL for redirect URIs",
        )

    def handle(self, *args, **options):
        base_url = options["keycloak_url"].rstrip("/")
        realm = options["realm"]
        frontend_url = options["frontend_url"].rstrip("/")

        # ── Step 1: Get admin access token ──
        self.stdout.write("Authenticating with Keycloak admin API...")
        try:
            token = self._get_admin_token(
                base_url,
                options["admin_user"],
                options["admin_password"],
            )
        except Exception as exc:
            raise CommandError(f"Failed to authenticate with Keycloak: {exc}")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # ── Step 2: Create realm ──
        self._create_realm(base_url, realm, headers)

        # ── Step 3: Create web-app client (public, PKCE) ──
        self._create_web_client(base_url, realm, headers, frontend_url)

        # ── Step 4: Create service-account client (confidential) ──
        self._create_service_client(base_url, realm, headers)

        # ── Step 5: Add custom protocol mappers ──
        self._add_protocol_mappers(base_url, realm, headers)

        self.stdout.write(self.style.SUCCESS(
            f"\nKeycloak realm '{realm}' configured successfully!\n"
            f"  JWKS endpoint: {base_url}/realms/{realm}/protocol/openid-connect/certs\n"
            f"  Token endpoint: {base_url}/realms/{realm}/protocol/openid-connect/token\n"
            f"  Admin console: {base_url}/admin/{realm}/console\n"
        ))

    def _get_admin_token(self, base_url: str, username: str, password: str) -> str:
        resp = requests.post(
            f"{base_url}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials"
                if username == "client"
                else "password",
                "client_id": "admin-cli",
                "username": username,
                "password": password,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _create_realm(self, base_url: str, realm: str, headers: dict):
        self.stdout.write(f"Creating realm '{realm}'...")
        resp = requests.get(f"{base_url}/admin/realms/{realm}", headers=headers, timeout=10)
        if resp.status_code == 200:
            self.stdout.write(self.style.WARNING(f"  Realm '{realm}' already exists — skipping."))
            return

        resp = requests.post(
            f"{base_url}/admin/realms",
            json={
                "realm": realm,
                "enabled": True,
                "displayName": "Healthcare SaaS",
                "registrationAllowed": False,
                "loginWithEmailAllowed": True,
                "duplicateEmailsAllowed": False,
                "resetPasswordAllowed": True,
                "bruteForceProtected": True,
                "permanentLockout": False,
                "maxFailureWaitSeconds": 900,
                "failureFactor": 5,
                "sslRequired": "external",
                "accessTokenLifespan": 900,  # 15 minutes
                "ssoSessionMaxLifespan": 86400,  # 24 hours
                "offlineSessionMaxLifespan": 604800,  # 7 days
                "passwordPolicy": (
                    "length(12) and upperCase(1) and lowerCase(1) "
                    "and digits(1) and specialChars(1) and notUsername"
                ),
            },
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f"  Realm '{realm}' created."))
        else:
            raise CommandError(f"Failed to create realm: {resp.status_code} {resp.text}")

    def _create_web_client(self, base_url: str, realm: str, headers: dict, frontend_url: str):
        client_id = "web-app"
        self.stdout.write(f"Creating client '{client_id}'...")

        # Check if exists
        resp = requests.get(
            f"{base_url}/admin/realms/{realm}/clients",
            params={"clientId": client_id},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200 and resp.json():
            self.stdout.write(self.style.WARNING(f"  Client '{client_id}' already exists — skipping."))
            return

        resp = requests.post(
            f"{base_url}/admin/realms/{realm}/clients",
            json={
                "clientId": client_id,
                "name": "Healthcare SaaS Web Application",
                "enabled": True,
                "publicClient": True,
                "standardFlowEnabled": True,
                "directAccessGrantsEnabled": True,
                "serviceAccountsEnabled": False,
                "redirectUris": [
                    f"{frontend_url}/*",
                    "http://localhost:3000/*",
                    "http://localhost:8000/*",
                ],
                "webOrigins": [
                    frontend_url,
                    "http://localhost:3000",
                    "http://localhost:8000",
                ],
                "attributes": {
                    "pkce.code.challenge.method": "S256",
                },
                "protocol": "openid-connect",
                "fullScopeAllowed": True,
            },
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f"  Client '{client_id}' created (public, PKCE)."))
        else:
            raise CommandError(f"Failed to create client '{client_id}': {resp.status_code} {resp.text}")

    def _create_service_client(self, base_url: str, realm: str, headers: dict):
        client_id = "service-account"
        self.stdout.write(f"Creating client '{client_id}'...")

        resp = requests.get(
            f"{base_url}/admin/realms/{realm}/clients",
            params={"clientId": client_id},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200 and resp.json():
            self.stdout.write(self.style.WARNING(f"  Client '{client_id}' already exists — skipping."))
            return

        resp = requests.post(
            f"{base_url}/admin/realms/{realm}/clients",
            json={
                "clientId": client_id,
                "name": "Healthcare SaaS Service Account",
                "enabled": True,
                "publicClient": False,
                "standardFlowEnabled": False,
                "directAccessGrantsEnabled": False,
                "serviceAccountsEnabled": True,
                "clientAuthenticatorType": "client-secret",
                "protocol": "openid-connect",
            },
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 201:
            self.stdout.write(self.style.SUCCESS(f"  Client '{client_id}' created (confidential)."))
            # Retrieve and display the generated secret
            resp2 = requests.get(
                f"{base_url}/admin/realms/{realm}/clients",
                params={"clientId": client_id},
                headers=headers,
                timeout=10,
            )
            if resp2.ok and resp2.json():
                internal_id = resp2.json()[0]["id"]
                secret_resp = requests.get(
                    f"{base_url}/admin/realms/{realm}/clients/{internal_id}/client-secret",
                    headers=headers,
                    timeout=10,
                )
                if secret_resp.ok:
                    secret = secret_resp.json().get("value", "")
                    self.stdout.write(f"  Client secret: {secret}")
        else:
            raise CommandError(f"Failed to create client: {resp.status_code} {resp.text}")

    def _add_protocol_mappers(self, base_url: str, realm: str, headers: dict):
        """Add phone and given_name/family_name mappers to web-app client."""
        self.stdout.write("Adding protocol mappers...")

        # Get web-app client internal ID
        resp = requests.get(
            f"{base_url}/admin/realms/{realm}/clients",
            params={"clientId": "web-app"},
            headers=headers,
            timeout=10,
        )
        if not resp.ok or not resp.json():
            self.stdout.write(self.style.WARNING("  Could not find web-app client for mappers."))
            return

        client_internal_id = resp.json()[0]["id"]

        mappers = [
            {
                "name": "phone",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "config": {
                    "user.attribute": "phone",
                    "claim.name": "phone",
                    "jsonType.label": "String",
                    "id.token.claim": "true",
                    "access.token.claim": "true",
                    "userinfo.token.claim": "true",
                },
            },
        ]

        for mapper in mappers:
            resp = requests.post(
                f"{base_url}/admin/realms/{realm}/clients/{client_internal_id}/protocol-mappers/models",
                json=mapper,
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 201:
                self.stdout.write(self.style.SUCCESS(f"  Mapper '{mapper['name']}' added."))
            elif resp.status_code == 409:
                self.stdout.write(self.style.WARNING(f"  Mapper '{mapper['name']}' already exists."))
            else:
                self.stdout.write(self.style.WARNING(
                    f"  Mapper '{mapper['name']}' failed: {resp.status_code}"
                ))

        self.stdout.write(self.style.SUCCESS("  Protocol mappers configured."))
