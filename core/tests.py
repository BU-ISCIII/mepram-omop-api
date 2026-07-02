from io import StringIO
from unittest.mock import patch

import jwt
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from core.api.authentication import (
    KeycloakJWTAuthentication,
    decode_and_validate_keycloak_token,
)


KEYCLOAK_SETTINGS = {
    "issuer": "https://keycloak.local/realms/ciberisciii_datahub",
    "jwks_url": (
        "https://keycloak.local/realms/ciberisciii_datahub/"
        "protocol/openid-connect/certs"
    ),
    "audience": "mepram-api",
    "client_id": "pathocore-web",
    "jwks_cache_ttl_seconds": 300,
    "jwks_timeout_seconds": 5,
}

TOKEN_PAYLOAD = {
    "sub": "user-123",
    "preferred_username": "alice",
    "groups": ["/use-cases/mepram/labs/lab1/viewer"],
    "iss": KEYCLOAK_SETTINGS["issuer"],
    "aud": KEYCLOAK_SETTINGS["audience"],
    "exp": 9999999999,
}


class KeycloakAuthenticationTests(SimpleTestCase):
    @patch(
        "core.api.authentication._get_keycloak_settings",
        return_value=KEYCLOAK_SETTINGS,
    )
    @patch("core.api.authentication._get_signing_key", return_value="public-key")
    @patch("core.api.authentication.jwt.decode", return_value=TOKEN_PAYLOAD)
    @patch(
        "core.api.authentication.jwt.get_unverified_header",
        return_value={"alg": "RS256", "kid": "kid-1"},
    )
    def test_authenticate_returns_token_user(
        self,
        header_mock,
        decode_mock,
        signing_key_mock,
        settings_mock,
    ):
        request = APIRequestFactory().get(
            "/v1/cohort/summary",
            HTTP_AUTHORIZATION="Bearer token-value",
        )

        user, auth = KeycloakJWTAuthentication().authenticate(request)

        self.assertEqual(user.id, "user-123")
        self.assertEqual(user.username, "alice")
        self.assertEqual(user.groups, ["/use-cases/mepram/labs/lab1/viewer"])
        self.assertEqual(auth, TOKEN_PAYLOAD)
        decode_mock.assert_called_once_with(
            "token-value",
            "public-key",
            algorithms=["RS256"],
            issuer=KEYCLOAK_SETTINGS["issuer"],
            audience=KEYCLOAK_SETTINGS["audience"],
            options={"require": ["iss", "aud", "sub"]},
        )

    @patch(
        "core.api.authentication._get_keycloak_settings",
        return_value=KEYCLOAK_SETTINGS,
    )
    @patch("core.api.authentication._get_signing_key", return_value="public-key")
    @patch("core.api.authentication.jwt.decode", side_effect=jwt.InvalidAudienceError)
    @patch(
        "core.api.authentication.jwt.get_unverified_header",
        return_value={"alg": "RS256", "kid": "kid-1"},
    )
    def test_decode_rejects_wrong_audience(
        self,
        header_mock,
        decode_mock,
        signing_key_mock,
        settings_mock,
    ):
        with self.assertRaisesMessage(AuthenticationFailed, "Invalid token audience"):
            decode_and_validate_keycloak_token("token-value")

    @patch(
        "core.api.authentication._get_keycloak_settings",
        return_value=KEYCLOAK_SETTINGS,
    )
    @patch("core.api.authentication._get_signing_key", return_value="public-key")
    @patch("core.api.authentication.jwt.decode", side_effect=jwt.InvalidIssuerError)
    @patch(
        "core.api.authentication.jwt.get_unverified_header",
        return_value={"alg": "RS256", "kid": "kid-1"},
    )
    def test_decode_rejects_wrong_issuer(
        self,
        header_mock,
        decode_mock,
        signing_key_mock,
        settings_mock,
    ):
        with self.assertRaisesMessage(AuthenticationFailed, "Invalid token issuer"):
            decode_and_validate_keycloak_token("token-value")

    @patch(
        "core.api.authentication._get_keycloak_settings",
        return_value={**KEYCLOAK_SETTINGS, "issuer": ""},
    )
    def test_decode_requires_keycloak_configuration(self, settings_mock):
        with self.assertRaisesMessage(
            AuthenticationFailed,
            "missing MEPRAM_KEYCLOAK_ISSUER",
        ):
            decode_and_validate_keycloak_token("token-value")

    @patch(
        "core.api.authentication._get_keycloak_settings",
        return_value=KEYCLOAK_SETTINGS,
    )
    @patch(
        "core.api.authentication.jwt.get_unverified_header",
        return_value={"alg": "HS256", "kid": "kid-1"},
    )
    def test_decode_rejects_non_rs256_tokens(self, header_mock, settings_mock):
        with self.assertRaisesMessage(
            AuthenticationFailed,
            "Unsupported token signing algorithm",
        ):
            decode_and_validate_keycloak_token("token-value")


@override_settings(MEPRAM_AUTH_REQUIRED=True, ALLOWED_HOSTS=["testserver"])
class EndpointSecurityTests(SimpleTestCase):
    def test_health_endpoint_is_public(self):
        payload = {
            "status": "UP",
            "schema": "mepram_omop_api",
            "tables": [],
            "checked_at": "2026-01-01T00:00:00+00:00",
        }
        with patch("core.api.v1.views.health.health_check", return_value=payload):
            response = Client().get("/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), payload)

    def test_data_endpoint_requires_bearer_token(self):
        response = Client().get("/v1/cohort/summary")

        self.assertEqual(response.status_code, 401)
        self.assertIn("Bearer", response.headers["WWW-Authenticate"])

    def test_swagger_redirects_anonymous_users_to_admin_login(self):
        response = Client().get("/v1/swagger/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.headers["Location"])


@override_settings(MEPRAM_AUTH_REQUIRED=False, ALLOWED_HOSTS=["testserver"])
class ReportsEndpointTests(SimpleTestCase):
    def test_full_report_post_requires_superuser(self):
        response = Client().post(
            "/v1/cohort/report",
            data={"summary_name": "Test report"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_full_report_endpoint_returns_report_payload(self):
        test_payload = {
            "summary_name": "Descriptive Report from June",
            "scope_key": "sepsis_report_full",
            "filters_hash": "",
            "filters": "",
            "payload": {
                "report": {
                    "date": "2026-06-30",
                    "title": "Descriptive Report",
                    "author": "MePRAM WP1-Team",
                    "summary": "Report covering 3913 hospital emergency episodes.",
                    "subtitle": "Use case: 'Sepsis in Hospital Emergencies'",
                    "generator": "A report generated by the MePRAM API",
                    "total_episodes": 2000,
                    "content_inventory": {
                    "note": "This is a test note for the report content inventory.",
                    "sections": 1,
                    "data_tables": 1
                    }
                },
                "sections": [
                    {
                    "title": "Sociodemographic - Patients - By sex",
                    "tables": [
                        "sociodemographic_patients_by_sex"
                    ]
                    }
                ],
                "data_tables": {
                    "sociodemographic_patients_by_sex": {
                    "rows": [
                        [
                        "MALE",
                        943,
                        0.4715
                        ],
                        [
                        "FEMALE",
                        1057,
                        0.5285
                        ]
                    ],
                    "title": "By sex",
                    "n_rows": 2,
                    "columns": [
                        "Sex",
                        "N patients",
                        "Percent"
                    ],
                    "default_order": []
                    }
                }
            },
            "created_at": "2026-07-01T12:00:00Z",
            "updated_at": "2026-07-01T12:00:00Z",
        }
        
        with patch("core.api.v1.views.reports.full_report", return_value=test_payload):
            response = Client().get("/v1/cohort/report")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), test_payload)


@override_settings(ALLOWED_HOSTS=["testserver"])
class DocumentationStaffAccessTests(TestCase):
    def test_swagger_is_available_to_staff_users(self):
        user = get_user_model().objects.create_user(
            username="swagger-admin",
            password="secret",
            is_staff=True,
        )
        client = Client()
        client.force_login(user)

        response = client.get("/v1/swagger/")

        self.assertEqual(response.status_code, 200)


class DefaultSuperuserCommandTests(TestCase):
    @override_settings(
        MEPRAM_CREATE_DEFAULT_SUPERUSER=True,
        DJANGO_SUPERUSER_USERNAME="admin",
        DJANGO_SUPERUSER_EMAIL="admin@example.org",
        DJANGO_SUPERUSER_PASSWORD="admin_pass",
    )
    def test_creates_default_superuser(self):
        output = StringIO()

        call_command("ensure_default_superuser", stdout=output)

        user = get_user_model().objects.get(username="admin")
        self.assertEqual(user.email, "admin@example.org")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("admin_pass"))
        self.assertIn("Created default superuser", output.getvalue())

    @override_settings(
        MEPRAM_CREATE_DEFAULT_SUPERUSER=True,
        DJANGO_SUPERUSER_USERNAME="admin",
        DJANGO_SUPERUSER_EMAIL="new@example.org",
        DJANGO_SUPERUSER_PASSWORD="new_pass",
    )
    def test_updates_existing_default_superuser(self):
        get_user_model().objects.create_user(
            username="admin",
            email="old@example.org",
            password="old_pass",
            is_staff=False,
            is_superuser=False,
        )

        call_command("ensure_default_superuser", stdout=StringIO())

        user = get_user_model().objects.get(username="admin")
        self.assertEqual(user.email, "new@example.org")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("new_pass"))

    @override_settings(MEPRAM_CREATE_DEFAULT_SUPERUSER=False)
    def test_skips_when_disabled(self):
        output = StringIO()

        call_command("ensure_default_superuser", stdout=output)

        self.assertFalse(get_user_model().objects.exists())
        self.assertIn("Default superuser creation disabled", output.getvalue())
