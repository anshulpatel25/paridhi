"""Tests for Paridhi OAuth 2.1 authentication integration and provider factory."""

from unittest.mock import MagicMock, patch

import pytest
from fastmcp.server.auth.oidc_proxy import OIDCConfiguration, OIDCProxy
from fastmcp.server.auth.providers.github import GitHubProvider
from fastmcp.server.auth.providers.google import GoogleProvider
from pydantic import AnyHttpUrl

from paridhi.core.config import Settings
from paridhi.domain.exceptions import AuthConfigurationError
from paridhi.infrastructure.auth import get_auth_provider
from paridhi.infrastructure.mock import MockSpatialProvider
from paridhi.presentation.server import create_server


def test_auth_disabled_by_default() -> None:
    """When auth_enabled is False, get_auth_provider returns None."""
    settings = Settings(auth_enabled=False, _env_file=None)  # type: ignore[call-arg]
    provider = get_auth_provider(settings)
    assert provider is None


def test_auth_explicitly_none_provider() -> None:
    """When auth_provider is 'none', get_auth_provider returns None even if auth_enabled is True."""
    settings = Settings(
        auth_enabled=True,
        auth_provider="none",
        _env_file=None,  # type: ignore[call-arg]
    )
    provider = get_auth_provider(settings)
    assert provider is None


def test_google_auth_missing_client_id_raises_error() -> None:
    """When Google OAuth is enabled without client_id, AuthConfigurationError is raised."""
    settings = Settings(
        auth_enabled=True,
        auth_provider="google",
        google_client_id=None,
        _env_file=None,  # type: ignore[call-arg]
    )
    with pytest.raises(AuthConfigurationError, match="Google OAuth Client ID is missing"):
        get_auth_provider(settings)


def test_google_auth_provider_instantiation() -> None:
    """Verify GoogleProvider is instantiated with provided settings."""
    settings = Settings(
        auth_enabled=True,
        auth_provider="google",
        google_client_id="123456789.apps.googleusercontent.com",
        google_client_secret="GOCSPX-secret123",
        auth_base_url="http://localhost:8000",
        auth_jwt_signing_key="custom-jwt-secret-key",
        _env_file=None,  # type: ignore[call-arg]
    )
    provider = get_auth_provider(settings)
    assert provider is not None
    assert isinstance(provider, GoogleProvider)
    assert provider._upstream_client_id == "123456789.apps.googleusercontent.com"
    assert (
        provider._upstream_client_secret.get_secret_value() == "GOCSPX-secret123"
        if provider._upstream_client_secret
        else False
    )


def test_github_auth_missing_credentials_raises_error() -> None:
    """When GitHub OAuth is selected without credentials, AuthConfigurationError is raised."""
    settings = Settings(
        auth_enabled=True,
        auth_provider="github",
        github_client_id=None,
        github_client_secret=None,
        _env_file=None,  # type: ignore[call-arg]
    )
    with pytest.raises(AuthConfigurationError, match="GitHub OAuth requires both"):
        get_auth_provider(settings)


def test_github_auth_provider_instantiation() -> None:
    """Verify GitHubProvider is instantiated with provided settings."""
    settings = Settings(
        auth_enabled=True,
        auth_provider="github",
        github_client_id="github-client-123",
        github_client_secret="github-secret-abc",
        auth_base_url="http://localhost:8000",
        _env_file=None,  # type: ignore[call-arg]
    )
    provider = get_auth_provider(settings)
    assert provider is not None
    assert isinstance(provider, GitHubProvider)
    assert provider._upstream_client_id == "github-client-123"
    assert (
        provider._upstream_client_secret.get_secret_value() == "github-secret-abc"
        if provider._upstream_client_secret
        else False
    )


def test_oidc_auth_missing_credentials_raises_error() -> None:
    """When generic OIDC is selected without config_url, AuthConfigurationError is raised."""
    settings = Settings(
        auth_enabled=True,
        auth_provider="oidc",
        oidc_config_url=None,
        oidc_client_id=None,
        _env_file=None,  # type: ignore[call-arg]
    )
    with pytest.raises(AuthConfigurationError, match="Generic OIDC provider requires both"):
        get_auth_provider(settings)


def test_oidc_auth_provider_instantiation() -> None:
    """Verify OIDCProxy is instantiated with mocked OIDC discovery."""
    mock_cfg = MagicMock(spec=OIDCConfiguration)
    mock_cfg.authorization_endpoint = AnyHttpUrl("https://idp.example.com/auth")
    mock_cfg.token_endpoint = AnyHttpUrl("https://idp.example.com/token")
    mock_cfg.revocation_endpoint = None
    mock_cfg.service_documentation = None

    settings = Settings(
        auth_enabled=True,
        auth_provider="oidc",
        oidc_config_url="https://idp.example.com/.well-known/openid-configuration",
        oidc_client_id="oidc-client-123",
        oidc_client_secret="oidc-secret-abc",
        auth_base_url="http://localhost:8000",
        _env_file=None,  # type: ignore[call-arg]
    )

    with (
        patch.object(OIDCProxy, "get_oidc_configuration", return_value=mock_cfg),
        patch.object(OIDCProxy, "get_token_verifier", return_value=MagicMock()),
    ):
        provider = get_auth_provider(settings)
        assert provider is not None
        assert isinstance(provider, OIDCProxy)
        assert provider._upstream_client_id == "oidc-client-123"


def test_unsupported_auth_provider_raises_error() -> None:
    """When an unsupported auth provider string is supplied, AuthConfigurationError is raised."""
    settings = Settings(
        auth_enabled=True,
        auth_provider="unsupported_idp",
        _env_file=None,  # type: ignore[call-arg]
    )
    with pytest.raises(AuthConfigurationError, match="Unsupported OAuth provider"):
        get_auth_provider(settings)


def test_create_server_with_auth_injection() -> None:
    """Verify create_server assigns injected AuthProvider to FastMCP."""
    settings = Settings(
        auth_enabled=True,
        auth_provider="google",
        google_client_id="test-client.apps.googleusercontent.com",
        google_client_secret="test-secret",
        auth_base_url="http://localhost:8000",
        _env_file=None,  # type: ignore[call-arg]
    )
    server = create_server(settings=settings, provider=MockSpatialProvider())
    assert server.auth is not None
    assert isinstance(server.auth, GoogleProvider)


@pytest.mark.asyncio
async def test_dynamic_client_registration_endpoint() -> None:
    """Verify FastMCP exposes RFC 7591 Dynamic Client Registration endpoint."""
    import httpx

    settings = Settings(
        auth_enabled=True,
        auth_provider="google",
        google_client_id="test-client.apps.googleusercontent.com",
        google_client_secret="test-secret",
        auth_base_url="http://localhost:8000",
        _env_file=None,  # type: ignore[call-arg]
    )
    server = create_server(settings=settings, provider=MockSpatialProvider())
    app = server.http_app(transport="http")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost:8000"
    ) as client:
        # 1. Discover OAuth metadata
        meta_resp = await client.get("/.well-known/oauth-authorization-server")
        assert meta_resp.status_code == 200
        meta_data = meta_resp.json()
        assert meta_data["registration_endpoint"] == "http://localhost:8000/register"
        assert meta_data.get("client_id_metadata_document_supported") is True

        # 2. Register dynamic client (e.g. Gemini Spark)
        reg_payload = {
            "client_name": "Gemini Spark",
            "redirect_uris": ["http://localhost:8080/callback"],
            "token_endpoint_auth_method": "none",
        }
        reg_resp = await client.post("/register", json=reg_payload)
        assert reg_resp.status_code == 201
        reg_data = reg_resp.json()
        assert "client_id" in reg_data
        assert reg_data["client_name"] == "Gemini Spark"
