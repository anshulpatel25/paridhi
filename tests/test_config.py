"""Tests for Paridhi configuration management."""

from paridhi.core.config import Settings, get_settings


def test_default_settings() -> None:
    """Verify default settings values."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.server_name == "Paridhi"
    assert settings.min_radius_meters == 100.0
    assert settings.max_radius_meters == 50000.0
    assert settings.default_radius_meters == 1000.0
    assert settings.transport == "stdio"


def test_settings_singleton() -> None:
    """Verify get_settings returns a cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_settings_server_version_override() -> None:
    """Verify server_version can be supplied as input."""
    custom_version = "1.2.3"
    settings = Settings(server_version=custom_version, _env_file=None)  # type: ignore[call-arg]
    assert settings.server_version == custom_version
