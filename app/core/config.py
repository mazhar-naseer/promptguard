from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    secret_key: str = "insecure-dev-key-change-me"
    database_url: str = "sqlite:///./data/promptguard.db"

    access_token_expire_minutes: int = 60
    admin_username: str = "admin"
    admin_password: str = "change-this-password"
    admin_email: str = "admin@example.com"

    rules_config_path: str = "app/config/rules.json"
    scoring_config_path: str = "app/config/scoring_weights.json"
    max_prompt_length: int = 8000

    llm_judge_enabled: bool = False
    llm_judge_api_key: str = ""
    llm_judge_api_url: str = "https://api.openai.com/v1/chat/completions"
    llm_judge_model: str = "gpt-4o-mini"

    rate_limit_analyst: str = "60/minute"
    rate_limit_anonymous: str = "10/minute"


settings = Settings()
