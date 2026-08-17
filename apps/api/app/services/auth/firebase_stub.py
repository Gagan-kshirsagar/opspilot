"""Firebase auth provider STUB — proves the pluggable seam.

None of these methods are implemented.  Setting OPSPILOT_AUTH_PROVIDER=firebase
will surface a ``NotImplementedError`` at the provider boundary, proving no
other code is coupled to the JWT implementation.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth.base import AuthUser, TokenClaims, TokenPair

_MSG = "Firebase auth provider is not yet implemented"


class FirebaseAuthProvider:
    """Placeholder — every method raises ``NotImplementedError``."""

    async def authenticate(
        self, email: str, password: str, session: AsyncSession
    ) -> AuthUser | None:
        raise NotImplementedError(_MSG)

    async def create_user(
        self, email: str, password: str, name: str, session: AsyncSession
    ) -> AuthUser:
        raise NotImplementedError(_MSG)

    def issue_tokens(self, user: AuthUser) -> TokenPair:
        raise NotImplementedError(_MSG)

    def verify_token(self, token: str) -> TokenClaims:
        raise NotImplementedError(_MSG)

    async def create_guest(self, session: AsyncSession) -> AuthUser:
        raise NotImplementedError(_MSG)
