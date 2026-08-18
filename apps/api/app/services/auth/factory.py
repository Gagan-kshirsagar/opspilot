"""Auth provider factory — returns the right AuthProvider based on config."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings
from app.services.auth.base import AuthProvider


@lru_cache(maxsize=1)
def get_auth_provider(settings: Settings | None = None) -> AuthProvider:
    """Return the configured auth provider (singleton).

    Reads ``settings.AUTH_PROVIDER`` to pick the backend:
    - ``"jwt"``  → :class:`JwtAuthProvider`
    - ``"firebase"`` → :class:`FirebaseAuthProvider` (stub, will raise)

    Raises ``ValueError`` for unknown provider names.
    """
    if settings is None:
        from app.core.config import get_settings

        settings = get_settings()

    provider_name = settings.AUTH_PROVIDER.lower()

    if provider_name == "jwt":
        from app.services.auth.jwt_provider import JwtAuthProvider

        return JwtAuthProvider(settings)

    if provider_name == "firebase":
        from app.services.auth.firebase_stub import FirebaseAuthProvider

        return FirebaseAuthProvider()

    raise ValueError(
        f"Unknown auth provider: {provider_name!r}. Supported: 'jwt', 'firebase'."
    )
