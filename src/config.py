from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"


class AppEnv(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    app_env: AppEnv = AppEnv.DEVELOPMENT

    @property
    def is_prod(self) -> bool:
        return self.app_env == AppEnv.PRODUCTION

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env")


settings = Settings()
