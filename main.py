import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.user import router, set_bot_commands
from database.methods import init_db
from config_data.config import Config, load_config
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.tracker import track_prices
from aiogram.client.session.aiohttp import AiohttpSession

session = AiohttpSession(proxy="http://proxy.server:1080")

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

async def main():
    setup_logging()

    # Загрузка конфигурации
    config: Config = load_config()

    # Инициализация бота
    bot = Bot(token=config.tg_bot.token, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализация базы данных
    await init_db()

    # Установка команд меню
    await set_bot_commands(bot)

    # Регистрация маршрутов
    dp.include_router(router)

    # Создание планировщика
    scheduler = AsyncIOScheduler()

    # Добавление задачи для отслеживания цен через определенное количество времени
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        track_prices,
        "interval",
        minutes=2,
        args=[bot]
    )

    scheduler.start()

    # Запуск бота
    logging.info("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())