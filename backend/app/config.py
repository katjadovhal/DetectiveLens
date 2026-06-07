from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://detectivelens:detectivelens@localhost:5432/detectivelens"
    frontend_url: str = "http://localhost:5173"
    port: int = 3001
    demo_user_id: str = "demo-user-id"


settings = Settings()
