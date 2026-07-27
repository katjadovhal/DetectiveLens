from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: str = "data"
    frontend_url: str = "http://localhost:5173"
    port: int = 3001
    demo_user_id: str = "demo-user-id"

    hint_engine_enabled: bool = False
    hint_model: str = "qwen3:4b"
    ollama_base_url: str = "http://localhost:11434"
    hint_timeout_seconds: float = 8.0
    hint_cache_enabled: bool = True
    hint_prompt_version: str = "v1"
    hint_temperature: float = 0.1


settings = Settings()
