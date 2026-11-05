from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM — Novita (OpenAI-compatible)
    novita_api_key: str = ""
    novita_base_url: str = "https://api.novita.ai/v3/openai"
    novita_model: str = "deepseek/deepseek-v3-0324"

    # YouTube
    youtube_client_secrets_file: str = "config/client_secrets.json"
    youtube_token_file: str = "config/token.json"
    default_privacy_status: str = "unlisted"

    # B-roll
    pexels_api_key: str = ""

    # Pipeline defaults
    max_clips_per_video: int = 5
    output_dir: str = "temp"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
