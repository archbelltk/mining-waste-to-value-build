"""Supabase JWT verification.

Supabase Auth issues JWTs signed with the project's JWT secret. Because
FastAPI knows that secret, it verifies tokens locally (`jwt.decode`) instead
of calling back to Supabase on every request — no network round-trip per
request, unlike a session-lookup auth scheme.

Like what you know: this is the same shape as verifying a NextAuth/Clerk JWT
with a shared secret in Express middleware — decode, check signature +
expiry, trust the claims.
"""

from dataclasses import dataclass

import jwt
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None


def decode_access_token(token: str) -> AuthenticatedUser:
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenError("token missing 'sub' claim")

    return AuthenticatedUser(id=subject, email=payload.get("email"))


def unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
