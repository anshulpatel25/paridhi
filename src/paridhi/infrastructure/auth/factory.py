"""Authentication provider factory for FastMCP OAuth 2.1 integration."""

import logging
import secrets
from typing import cast

from fastmcp.server.auth import AuthProvider

from paridhi.core.config import Settings, get_settings
from paridhi.domain.exceptions import AuthConfigurationError

logger = logging.getLogger("paridhi.infrastructure.auth")


def _resolve_jwt_signing_key(configured_key: str | None, client_secret: str | None) -> str | None:
    """Resolve JWT signing key, generating an ephemeral key for public clients if needed."""
    if configured_key and configured_key.strip():
        return configured_key.strip()
    if client_secret and client_secret.strip():
        # FastMCP will derive key from client_secret
        return None
    # Public client without secret: generate secure ephemeral signing key
    logger.debug("Generating ephemeral JWT signing key for public OAuth client")
    return secrets.token_hex(32)


def get_auth_provider(settings: Settings | None = None) -> AuthProvider | None:
    """Instantiate and return the configured FastMCP OAuth AuthProvider.

    Supports pluggable identity providers:
    - 'google': Google OAuth 2.0 (GoogleProvider)
    - 'github': GitHub OAuth (GitHubProvider)
    - 'oidc' / 'generic': OpenID Connect Discovery (OIDCProxy)
    - 'none': Authentication disabled

    Returns:
        AuthProvider instance when auth is enabled, or None when disabled.

    Raises:
        AuthConfigurationError: When required IdP configuration is missing or invalid.
    """
    app_settings = settings or get_settings()

    if not app_settings.auth_enabled:
        logger.debug("Authentication is disabled (PARIDHI_AUTH_ENABLED=False)")
        return None

    provider_name = app_settings.auth_provider.lower().strip()
    base_url = app_settings.effective_auth_base_url

    if provider_name in ("none", "disabled", ""):
        logger.debug("Authentication provider set to '%s'; auth disabled", provider_name)
        return None

    if provider_name == "google":
        client_id = app_settings.google_client_id
        if not client_id or not client_id.strip():
            raise AuthConfigurationError(
                "Google OAuth Client ID is missing. Please set GOOGLE_CLIENT_ID or "
                "PARIDHI_GOOGLE_CLIENT_ID in your environment or .env file."
            )

        logger.info(
            "Initializing Google OAuth 2.0 provider (client_id: %s..., base_url: %s)",
            client_id[:12] if len(client_id) > 12 else client_id,
            base_url,
        )

        from fastmcp.server.auth.providers.google import GoogleProvider

        jwt_key = _resolve_jwt_signing_key(
            app_settings.auth_jwt_signing_key, app_settings.google_client_secret
        )

        return cast(
            AuthProvider,
            GoogleProvider(
                client_id=client_id.strip(),
                client_secret=(
                    app_settings.google_client_secret.strip()
                    if app_settings.google_client_secret
                    else None
                ),
                base_url=base_url,
                jwt_signing_key=jwt_key,
                required_scopes=app_settings.google_oauth_scopes,
                require_authorization_consent=app_settings.auth_require_consent,
                allowed_client_redirect_uris=app_settings.auth_allowed_redirect_uris,
            ),
        )

    if provider_name == "github":
        client_id = app_settings.github_client_id
        client_secret = app_settings.github_client_secret
        if not client_id or not client_secret:
            raise AuthConfigurationError(
                "GitHub OAuth requires both GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET."
            )

        logger.info("Initializing GitHub OAuth provider (base_url: %s)", base_url)

        from fastmcp.server.auth.providers.github import GitHubProvider

        return cast(
            AuthProvider,
            GitHubProvider(
                client_id=client_id.strip(),
                client_secret=client_secret.strip(),
                base_url=base_url,
                jwt_signing_key=app_settings.auth_jwt_signing_key,
                require_authorization_consent=app_settings.auth_require_consent,
                allowed_client_redirect_uris=app_settings.auth_allowed_redirect_uris,
            ),
        )

    if provider_name in ("oidc", "generic"):
        config_url = app_settings.oidc_config_url
        client_id = app_settings.oidc_client_id
        if not config_url or not client_id:
            raise AuthConfigurationError(
                "Generic OIDC provider requires both OIDC_CONFIG_URL and OIDC_CLIENT_ID."
            )

        logger.info(
            "Initializing OIDC provider (config_url: %s, base_url: %s)",
            config_url,
            base_url,
        )

        from fastmcp.server.auth.oidc_proxy import OIDCProxy

        jwt_key = _resolve_jwt_signing_key(
            app_settings.auth_jwt_signing_key, app_settings.oidc_client_secret
        )

        return cast(
            AuthProvider,
            OIDCProxy(
                config_url=config_url.strip(),
                client_id=client_id.strip(),
                client_secret=(
                    app_settings.oidc_client_secret.strip()
                    if app_settings.oidc_client_secret
                    else None
                ),
                base_url=base_url,
                jwt_signing_key=jwt_key,
                require_authorization_consent=app_settings.auth_require_consent,
                allowed_client_redirect_uris=app_settings.auth_allowed_redirect_uris,
            ),
        )

    raise AuthConfigurationError(
        f"Unsupported OAuth provider '{provider_name}'. "
        "Supported providers are: 'google', 'github', 'oidc', or 'none'."
    )
