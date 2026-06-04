import json
import threading
from dataclasses import dataclass, field
from urllib.error import URLError
from urllib.request import urlopen

import jwt
from django.conf import settings
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

_JWKS_CACHE = {"expires_at": 0.0, "keys_by_kid": {}}
_JWKS_CACHE_LOCK = threading.Lock()


@dataclass
class KeycloakTokenUser:
    subject: str
    username: str
    groups: list[str] = field(default_factory=list)
    token_payload: dict = field(default_factory=dict)

    @property
    def id(self):
        return self.subject

    @property
    def pk(self):
        return self.subject

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return True

    def __str__(self):
        return self.username or self.subject


class KeycloakJWTAuthentication:
    www_authenticate_realm = "api"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth:
            return None
        if auth[0].lower() != b"bearer":
            return None
        if len(auth) != 2:
            raise AuthenticationFailed("Invalid bearer token header")
        try:
            token = auth[1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AuthenticationFailed("Invalid bearer token header") from exc

        payload = decode_and_validate_keycloak_token(token)
        user = KeycloakTokenUser(
            subject=str(payload["sub"]),
            username=str(payload.get("preferred_username") or payload["sub"]),
            groups=_normalize_groups(payload.get("groups")),
            token_payload=payload,
        )
        return user, payload

    def authenticate_header(self, request):
        return f'Bearer realm="{self.www_authenticate_realm}"'


def decode_and_validate_keycloak_token(token):
    keycloak_settings = _get_keycloak_settings()
    missing = [
        env_name
        for env_name, value in (
            ("MEPRAM_KEYCLOAK_ISSUER", keycloak_settings["issuer"]),
            ("MEPRAM_KEYCLOAK_JWKS_URL", keycloak_settings["jwks_url"]),
            ("MEPRAM_KEYCLOAK_AUDIENCE", keycloak_settings["audience"]),
            ("MEPRAM_KEYCLOAK_CLIENT_ID", keycloak_settings["client_id"]),
        )
        if not value
    ]
    if missing:
        raise AuthenticationFailed(
            "Keycloak authentication is not configured: missing " + ", ".join(missing)
        )

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise AuthenticationFailed("Invalid token header") from exc

    if header.get("alg") != "RS256":
        raise AuthenticationFailed("Unsupported token signing algorithm")

    signing_key = _get_signing_key(
        kid=header.get("kid"),
        jwks_url=keycloak_settings["jwks_url"],
        ttl_seconds=keycloak_settings["jwks_cache_ttl_seconds"],
        timeout_seconds=keycloak_settings["jwks_timeout_seconds"],
    )
    try:
        return jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=keycloak_settings["issuer"],
            audience=keycloak_settings["audience"],
            options={"require": ["iss", "aud", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationFailed("Token has expired") from exc
    except jwt.MissingRequiredClaimError as exc:
        raise AuthenticationFailed(
            f"Token is missing required claim: {exc.claim}"
        ) from exc
    except jwt.InvalidAudienceError as exc:
        raise AuthenticationFailed("Invalid token audience") from exc
    except jwt.InvalidIssuerError as exc:
        raise AuthenticationFailed("Invalid token issuer") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationFailed("Invalid token") from exc


def _get_signing_key(kid, jwks_url, ttl_seconds, timeout_seconds):
    import time

    now = time.time()
    with _JWKS_CACHE_LOCK:
        if now >= _JWKS_CACHE["expires_at"]:
            _JWKS_CACHE["keys_by_kid"] = _fetch_jwks(jwks_url, timeout_seconds)
            _JWKS_CACHE["expires_at"] = now + ttl_seconds
        keys_by_kid = _JWKS_CACHE["keys_by_kid"]

    key_data = keys_by_kid.get(kid)
    if key_data is None:
        with _JWKS_CACHE_LOCK:
            _JWKS_CACHE["keys_by_kid"] = _fetch_jwks(jwks_url, timeout_seconds)
            _JWKS_CACHE["expires_at"] = time.time() + ttl_seconds
            key_data = _JWKS_CACHE["keys_by_kid"].get(kid)

    if key_data is None:
        raise AuthenticationFailed("Token signing key not found")

    try:
        return jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
    except jwt.PyJWTError as exc:
        raise AuthenticationFailed("Invalid token signing key") from exc


def _fetch_jwks(jwks_url, timeout_seconds):
    try:
        with urlopen(jwks_url, timeout=timeout_seconds) as response:
            jwks = response.read().decode("utf-8")
    except URLError as exc:
        raise AuthenticationFailed("Unable to fetch Keycloak JWKS") from exc
    try:
        data = json.loads(jwks)
    except ValueError as exc:
        raise AuthenticationFailed("Invalid Keycloak JWKS response") from exc
    return {str(key.get("kid")): key for key in data.get("keys", []) if key.get("kid")}


def _normalize_groups(groups):
    if not isinstance(groups, list):
        return []
    return [str(group).strip() for group in groups if str(group).strip()]


def _get_keycloak_settings():
    return {
        "issuer": settings.MEPRAM_KEYCLOAK_ISSUER.strip(),
        "jwks_url": settings.MEPRAM_KEYCLOAK_JWKS_URL.strip(),
        "audience": _parse_audience_setting(settings.MEPRAM_KEYCLOAK_AUDIENCE),
        "client_id": settings.MEPRAM_KEYCLOAK_CLIENT_ID.strip(),
        "jwks_cache_ttl_seconds": settings.MEPRAM_KEYCLOAK_JWKS_CACHE_TTL_SECONDS,
        "jwks_timeout_seconds": settings.MEPRAM_KEYCLOAK_JWKS_TIMEOUT_SECONDS,
    }


def _parse_audience_setting(value):
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    values = [item.strip() for item in str(value).split(",") if item.strip()]
    if len(values) == 1:
        return values[0]
    return values
