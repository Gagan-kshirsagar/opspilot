"""JWT auth provider — concrete AuthProvider using passlib + python-jose."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User, UserRole, UserStatus
from app.repositories.user_repo import UserRepository
from app.services.auth.base import AuthUser, TokenClaims, TokenPair

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JwtAuthProvider:
    """AuthProvider backed by local bcrypt hashing and HS256 JWTs."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.JWT_SECRET
        self._algorithm = settings.JWT_ALGORITHM
        self._access_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self._refresh_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    # ── Protocol methods ──────────────────────────────────

    async def authenticate(
        self, email: str, password: str, session: AsyncSession
    ) -> AuthUser | None:
        """Verify email + password; return AuthUser or None."""
        repo = UserRepository(session)
        user = await repo.get_by_email(email)
        if user is None or user.password_hash is None:
            return None
        if not _pwd_context.verify(password, user.password_hash):
            return None
        return self._to_auth_user(user)

    async def create_user(
        self, email: str, password: str, name: str, session: AsyncSession
    ) -> AuthUser:
        """Hash the password, persist the user, and return AuthUser."""
        hashed = _pwd_context.hash(password)
        user = User(
            email=email,
            name=name,
            password_hash=hashed,
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
            is_guest=False,
        )
        repo = UserRepository(session)
        user = await repo.create(user)
        return self._to_auth_user(user)

    def issue_tokens(self, user: AuthUser) -> TokenPair:
        """Mint access (short-lived) and refresh (long-lived) JWTs."""
        now = datetime.now(UTC)
        access_exp = now + timedelta(minutes=self._access_minutes)
        refresh_exp = now + timedelta(days=self._refresh_days)

        access_payload = {
            "sub": str(user.id),
            "role": user.role,
            "type": "access",
            "exp": access_exp,
            "iat": now,
        }
        refresh_payload = {
            "sub": str(user.id),
            "role": user.role,
            "type": "refresh",
            "exp": refresh_exp,
            "iat": now,
        }

        access_token = jwt.encode(
            access_payload, self._secret, algorithm=self._algorithm
        )
        refresh_token = jwt.encode(
            refresh_payload, self._secret, algorithm=self._algorithm
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._access_minutes * 60,
        )

    def verify_token(self, token: str) -> TokenClaims:
        """Decode *token* or raise ``ValueError`` on any failure."""
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError as exc:
            raise ValueError(f"Invalid token: {exc}") from exc

        sub = payload.get("sub")
        role = payload.get("role")
        token_type = payload.get("type")
        if not sub or not role or not token_type:
            raise ValueError("Token missing required claims")

        return TokenClaims(sub=sub, role=role, type=token_type)

    async def create_guest(self, session: AsyncSession) -> AuthUser:
        """Create a throwaway guest user (no password)."""
        guest_id = uuid.uuid4()
        user = User(
            email=None,
            name=f"Guest-{str(guest_id)[:8]}",
            password_hash=None,
            role=UserRole.GUEST,
            status=UserStatus.ACTIVE,
            is_guest=True,
        )
        repo = UserRepository(session)
        user = await repo.create(user)
        return self._to_auth_user(user)

    # ── Helpers ───────────────────────────────────────────

    @staticmethod
    def _to_auth_user(user: User) -> AuthUser:
        """Map a SQLAlchemy User to the lightweight AuthUser dataclass."""
        return AuthUser(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_guest=user.is_guest,
        )
