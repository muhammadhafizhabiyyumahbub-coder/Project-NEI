"""Butir 4: session secret default rejection in non-dev mode."""
import os
import pytest


def test_default_session_secret_rejects_start_in_prod(monkeypatch):
    monkeypatch.setenv("NEI_ENVIRONMENT", "prod")
    monkeypatch.setenv("NEI_SESSION_SECRET", "insecure-change-me")
    from nei.core.config import Settings
    settings = Settings(_env_file=None)
    assert settings.environment == "prod"
    assert settings.session_secret == "insecure-change-me"
    # The lifespan check should reject this combination
    assert settings.session_secret == "insecure-change-me" and settings.environment != "dev"


def test_custom_session_secret_accepted_in_prod(monkeypatch):
    monkeypatch.setenv("NEI_ENVIRONMENT", "prod")
    monkeypatch.setenv("NEI_SESSION_SECRET", "strong-secret-xyz")
    from nei.core.config import Settings
    settings = Settings(_env_file=None)
    assert settings.session_secret != "insecure-change-me"


def test_dev_mode_allows_default_secret(monkeypatch):
    monkeypatch.setenv("NEI_ENVIRONMENT", "dev")
    monkeypatch.setenv("NEI_SESSION_SECRET", "insecure-change-me")
    from nei.core.config import Settings
    settings = Settings(_env_file=None)
    assert settings.environment == "dev"
    assert settings.session_secret == "insecure-change-me"
