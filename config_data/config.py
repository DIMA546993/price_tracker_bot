from dataclasses import dataclass
from environs import Env

@dataclass
class TrackerConfig:
    check_interval_minutes: int = 2  # Интервал проверки цен

@dataclass
class TgBot:
    token: str

@dataclass
class Config:
    tg_bot: TgBot
    tracker: TrackerConfig  # Добавлено поле tracker

def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(token=env("BOT_TOKEN")),
        tracker=TrackerConfig(check_interval_minutes=2)  # Передаем TrackerConfig
    )