from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_valid_demo_settings_load(settings_factory: Callable[..., Settings]) -> None:
    settings = settings_factory()

    assert settings.demo_mode is True
    assert settings.company_tz == "America/Los_Angeles"


def test_missing_required_secret_fails_fast_without_leaking_values(
    settings_factory: Callable[..., Settings],
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        settings_factory(session_secret=None)

    message = str(exc_info.value)
    assert "SESSION_SECRET" in message
    assert "k" * 44 not in message  # other secret values are never echoed


def test_short_secret_is_rejected(settings_factory: Callable[..., Settings]) -> None:
    with pytest.raises(ValidationError, match="LOG_HASH_PEPPER"):
        settings_factory(log_hash_pepper="too-short")


def test_gemini_key_required_unless_fake_provider(settings_factory: Callable[..., Settings]) -> None:
    with pytest.raises(ValidationError, match="GEMINI_API_KEY"):
        settings_factory(llm_provider="gemini", gemini_api_key=None)

    assert settings_factory(llm_provider="gemini", gemini_api_key="g" * 39).llm_provider == "gemini"


def test_real_google_mode_requires_oauth_client_and_bootstrap_owner(
    settings_factory: Callable[..., Settings],
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        settings_factory(demo_mode=False)

    message = str(exc_info.value)
    for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "BOOTSTRAP_OWNER_EMAIL"):
        assert name in message


def test_real_google_mode_loads_when_configured(settings_factory: Callable[..., Settings]) -> None:
    settings = settings_factory(
        demo_mode=False,
        google_client_id="client-id.apps.googleusercontent.com",
        google_client_secret="c" * 35,
        bootstrap_owner_email="Owner@JuniperRidge.example",
    )

    assert settings.bootstrap_owner_email == "owner@juniperridge.example"


def test_demo_mode_refuses_google_client_secret(settings_factory: Callable[..., Settings]) -> None:
    with pytest.raises(ValidationError, match="DEMO_MODE"):
        settings_factory(google_client_secret="c" * 35)


def test_invalid_company_timezone_is_rejected(settings_factory: Callable[..., Settings]) -> None:
    with pytest.raises(ValidationError, match="COMPANY_TZ"):
        settings_factory(company_tz="Mars/Olympus_Mons")


def test_api_docs_disabled_in_prod(settings_factory: Callable[..., Settings]) -> None:
    assert settings_factory(env="prod").api_docs_enabled is False
    assert settings_factory(env="dev").api_docs_enabled is True


def test_blank_env_values_are_treated_as_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_PROVIDER=fake\nGEMINI_API_KEY=\nGOOGLE_CLIENT_ID=\nGOOGLE_CLIENT_SECRET=\n"
        "BOOTSTRAP_OWNER_EMAIL=\n"
        f"SESSION_SECRET={'s' * 48}\nKEK_KEYS={'k' * 44}\nLOG_HASH_PEPPER={'p' * 40}\n",
        encoding="utf-8",
    )
    for name in ("GEMINI_API_KEY", "GOOGLE_CLIENT_SECRET", "BOOTSTRAP_OWNER_EMAIL"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=env_file)  # type: ignore[call-arg]

    assert settings.bootstrap_owner_email is None
    assert settings.google_client_secret is None
