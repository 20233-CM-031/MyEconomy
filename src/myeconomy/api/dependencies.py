"""HTTP authentication dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from myeconomy.application.identity import resolve_session
from myeconomy.domain.errors import AuthenticationError, AuthorizationError
from myeconomy.infrastructure.database import get_db
from myeconomy.infrastructure.models import AuthSession, User

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: AuthSession


def require_authentication(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError()
    user, auth_session = resolve_session(db, raw_token=credentials.credentials)
    return AuthContext(user=user, session=auth_session)


def require_verified_authentication(
    auth: AuthContext = Depends(require_authentication),
) -> AuthContext:
    """Require control of the account email before household/consent operations."""
    if not auth.user.email_verified:
        raise AuthorizationError("Verify your email address before using this feature.")
    return auth
