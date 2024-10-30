import os
from dataclasses import dataclass, asdict

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BaseConfig:
    def asdict(self):
        return asdict(self)


@dataclass
class DatabaseConfig(BaseConfig):
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", 5432)

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@dataclass
class BotConfig(BaseConfig):
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    ADMIN_LIST: str = os.getenv('ADMIN_LIST')
    ADMIN_NUMBER = os.getenv('ADMIN_NUMBER')
    CHANNELS = tuple(map(int, os.getenv('CHANNELS').split(',')))

    WEB_SERVER_HOST: str = os.getenv('WEB_SERVER_HOST')
    WEB_SERVER_PORT: int = int(os.getenv('WEB_SERVER_PORT', 8080))
    WEBHOOK_PATH = "/webhook"
    BASE_WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')

    @property
    def get_admin_list(self):
        return list(map(int, self.ADMIN_LIST.split(',')))


@dataclass
class Configuration:
    db = DatabaseConfig()
    bot = BotConfig()


conf = Configuration()
