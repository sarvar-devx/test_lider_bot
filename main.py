import asyncio
import logging
import sys

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import conf
from db import database
from handlers import main_router, admin_router, command_router
from utils.middlware import SubscriptionMiddleware


async def on_start(bot: Bot):
    await database.create_all()
    commands = [
        BotCommand(command='start', description="🏁 Bo'tni ishga tushirish"),
        BotCommand(command='myinfo', description="📝 Mening malumotlarim"),
        BotCommand(command='help', description="🆘 yordam"),
        BotCommand(command='dasturchi', description="👨🏼‍💻 Dasturchi"),
    ]
    await bot.set_my_commands(commands=commands)


async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    await bot.delete_my_commands()


async def main():
    dp = Dispatcher()
    dp.startup.register(on_start)
    dp.update.middleware(SubscriptionMiddleware())
    dp.shutdown.register(on_shutdown)
    dp.include_routers(
        admin_router,
        main_router,
        command_router,
    )
    bot = Bot(conf.bot.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
