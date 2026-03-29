from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe

import jwt
from django.conf import settings
from django.core.exceptions import PermissionDenied

from fca.users.models import MagicLinkTokenUse


@dataclass(frozen=True)
class MagicLinkClaims:
    email: str
    jti: str


class MagicLinkExpiredError(Exception):
    pass


class MagicLinkInvalidError(Exception):
    pass


def normalize_email(value: str) -> str:
    return value.strip().lower()


def is_allowed_email_domain(email: str) -> bool:
    email_normalized = normalize_email(email)
    domain = email_normalized.rsplit("@", 1)[-1]
    return domain == settings.MAGIC_LINK_ALLOWED_DOMAIN


def _jwt_secret() -> str:
    return settings.MAGIC_LINK_JWT_SECRET or settings.SECRET_KEY


def _token_jti(raw: str) -> str:
    return sha256(raw.encode("utf-8")).hexdigest()


def build_magic_link_token(email: str) -> str:
    if not is_allowed_email_domain(email):
        raise PermissionDenied("Only DSU email addresses are allowed.")
    now = datetime.now(tz=UTC)
    payload = {
        "eml": normalize_email(email),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.MAGIC_LINK_TTL_MINUTES)).timestamp()),
        "jti": token_urlsafe(24),
    }
    return jwt.encode(
        payload,
        _jwt_secret(),
        algorithm=settings.MAGIC_LINK_JWT_ALGORITHM,
    )


def parse_magic_link_token(token: str) -> MagicLinkClaims:
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[settings.MAGIC_LINK_JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise MagicLinkExpiredError from exc
    except jwt.InvalidTokenError as exc:
        raise MagicLinkInvalidError from exc

    email = normalize_email(payload.get("eml", ""))
    jti = str(payload.get("jti", "")).strip()
    if not email or not jti or not is_allowed_email_domain(email):
        raise MagicLinkInvalidError
    return MagicLinkClaims(email=email, jti=jti)


def consume_magic_link_jti(jti: str, email: str) -> bool:
    token_hash = _token_jti(jti)
    _, created = MagicLinkTokenUse.objects.get_or_create(
        jti=token_hash,
        defaults={"email": normalize_email(email)},
    )
    return created
