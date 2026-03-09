from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    core_port: int = Field(default=8000, alias="CORE_PORT")

    # IMPORTANT: include /api/v2 in the base URL (per your OpenAPI servers.url)
    coverity_base_url: str = Field(alias="COVERITY_BASE_URL")
    coverity_username: str = Field(alias="COVERITY_USERNAME")
    coverity_password: str = Field(alias="COVERITY_PASSWORD")

    # TLS verification ON by default (only used for https)
    coverity_tls_verify: bool = Field(default=True, alias="COVERITY_TLS_VERIFY")
    coverity_ca_bundle: str | None = Field(default=None, alias="COVERITY_CA_BUNDLE")

    # Safety limits
    max_limit: int = Field(default=200, alias="MAX_LIMIT")
    max_lookback_days: int = Field(default=365, alias="MAX_LOOKBACK_DAYS")
    http_timeout_seconds: int = Field(default=10, alias="HTTP_TIMEOUT_SECONDS")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

settings = Settings()
