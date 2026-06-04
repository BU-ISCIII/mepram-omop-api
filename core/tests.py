from unittest.mock import patch

import jwt
from django.contrib.auth import get_user_model
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
            "schema": "mepram_api",
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
