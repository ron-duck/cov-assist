from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    agent_port: int = Field(default=8090, alias="AGENT_PORT")
    agent_log_level: str = Field(default="INFO", alias="AGENT_LOG_LEVEL")
    gateway_base_url: str = Field(default="http://gateway:8080", alias="GATEWAY_BASE_URL")
    gateway_api_key: str = Field(alias="AGENT_GATEWAY_API_KEY")

    llm_base_url: str = Field(alias="LLM_BASE_URL")
    llm_model: str = Field(alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_timeout_seconds: float = Field(default=60.0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_tool_round_trips: int = Field(default=6, alias="LLM_MAX_TOOL_ROUND_TRIPS")
    llm_temperature: float = Field(default=0.0, alias="LLM_TEMPERATURE")


settings = Settings()
