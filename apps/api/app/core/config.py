import ssl
from functools import lru_cache
from typing import Any, Literal

from pydantic import AnyHttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DatabaseSSLMode = Literal["disable", "require", "verify-ca", "verify-full"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    app_name: str = "ML Workflow API"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://devuser:devpass@db:5432/devdb"
    database_ssl_mode: DatabaseSSLMode = "disable"
    database_ssl_root_cert: str | None = None

    supabase_url: AnyHttpUrl | None = None
    supabase_jwks_url: AnyHttpUrl | None = None
    supabase_jwt_audience: str = "authenticated"
    supabase_service_role_key: SecretStr | None = None
    supabase_storage_bucket: str = "attachments"
    bootstrap_admin_emails: str = ""

    @model_validator(mode="after")
    def validate_environment_security(self) -> "Settings":
        if self.app_env.lower() in {"production", "prod", "staging"} and self.database_ssl_mode == "disable":
            raise ValueError("database_ssl_mode cannot be 'disable' in production-like environments.")
        return self

    @property
    def resolved_supabase_jwks_url(self) -> str | None:
        if self.supabase_jwks_url is not None:
            return str(self.supabase_jwks_url)
        if self.supabase_url is None:
            return None
        return f"{str(self.supabase_url).rstrip('/')}/auth/v1/.well-known/jwks.json"

    @property
    def resolved_supabase_service_role_key(self) -> str | None:
        if self.supabase_service_role_key is None:
            return None
        return self.supabase_service_role_key.get_secret_value()

    def database_connect_args(self) -> dict[str, Any]:
        if self.database_ssl_mode == "disable":
            return {}

        ssl_context = ssl.create_default_context(cafile=self.database_ssl_root_cert)
        if self.database_ssl_mode == "require":
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        elif self.database_ssl_mode == "verify-ca":
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        else:
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        return {"ssl": ssl_context}


@lru_cache
def get_settings() -> Settings:
    return Settings()
