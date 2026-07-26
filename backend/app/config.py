from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: str = "data"
    frontend_url: str = "http://localhost:5173"
    port: int = 3001
    demo_user_id: str = "demo-user-id"


settings = Settings()
