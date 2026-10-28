from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    riot_api_key: str = ""
    # Account API uses a regional route, e.g. "asia", "americas", "europe"
    riot_regional_host: str = "asia"
    # Match-V5 also uses the regional route. SEA servers (VN2, SG2...) go through "sea".
    riot_match_host: str = "sea"
    database_url: str = "sqlite+aiosqlite:///./lol.db"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()