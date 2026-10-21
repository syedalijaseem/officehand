"""Application settings, loaded from environment variables.

Startup fails fast with the *names* of missing or invalid settings. Secret values are
never echoed in errors or logs.
"""

from functools import cached_property
from pathlib import Path
from typing import Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import EmailStr, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    # env_ignore_empty: a blank line like `GOOGLE_CLIENT_SECRET=` in .env means "unset", not "".
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True, env_ignore_empty=True)

    env: Literal["dev", "test", "prod"] = "dev"
    demo_mode: bool = True
    data_dir: Path = Path("./data")
    frontend_dist: Path = Path("../frontend/dist/frontend/browser")
    sample_data_dir: Path = Path("../sample_data")
    company_tz: str = "America/Los_Angeles"

    llm_provider: Literal["gemini", "fake"] = "gemini"
    gemini_api_key: SecretStr | None = None

    session_secret: SecretStr | None = None
    kek_keys: SecretStr | None = None
    log_hash_pepper: SecretStr | None = None

    google_client_id: str | None = None
    google_client_secret: SecretStr | None = None
    bootstrap_owner_email: EmailStr | None = None

    @field_validator("company_tz")
    @classmethod
    def _valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("COMPANY_TZ is not a valid IANA time zone") from exc
        return value

    @field_validator("bootstrap_owner_email")
    @classmethod
    def _lowercase_email(cls, value: str | None) -> str | None:
        return value.lower() if value else value

    @model_validator(mode="after")
    def _check_required_settings(self) -> Self:
        problems: list[str] = []

        for name in ("session_secret", "kek_keys", "log_hash_pepper"):
            secret: SecretStr | None = getattr(self, name)
            if secret is None:
                problems.append(f"{name.upper()} is required")
            elif len(secret.get_secret_value()) < MIN_SECRET_LENGTH:
                problems.append(f"{name.upper()} must be at least {MIN_SECRET_LENGTH} characters")

        if self.llm_provider == "gemini" and self.gemini_api_key is None:
            problems.append("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

        if self.demo_mode:
            if self.google_client_secret is not None:
                problems.append("GOOGLE_CLIENT_SECRET must not be set when DEMO_MODE=true (demo isolation)")
        else:
            if not self.google_client_id:
                problems.append("GOOGLE_CLIENT_ID is required when DEMO_MODE=false")
            if self.google_client_secret is None:
                problems.append("GOOGLE_CLIENT_SECRET is required when DEMO_MODE=false")
            if self.bootstrap_owner_email is None:
                problems.append("BOOTSTRAP_OWNER_EMAIL is required when DEMO_MODE=false")

        if problems:
            raise ValueError("Invalid configuration: " + "; ".join(problems))
        return self

    @cached_property
    def api_docs_enabled(self) -> bool:
        return self.env != "prod"

    @cached_property
    def database_path(self) -> Path:
        return self.data_dir / "officehand.db"
