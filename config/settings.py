from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra="ignore")

    OPENAI_API_KEY: str
    MONGODB_URI: str
    MONGODB_DB: str = 'travel_concierge'
    AMADEUS_CLIENT_ID: str = ''
    AMADEUS_CLIENT_SECRET: str = ''
    GOOGLE_PLACES_API_KEY: str = ''
    APP_BASE_URL: str = 'http://localhost:8000'
    DEFAULT_HOME_CURRENCY: str = 'INR'

settings = Settings()