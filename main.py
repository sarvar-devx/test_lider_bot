import asyncio
import logging
import sys

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

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
    admin_commands = [BotCommand(command="elon", description="📢 Foydalanuvchilarga elon berish")] + user_commands
    for admin_id in conf.bot.get_admin_list:
        await bot.set_my_commands(admin_commands, BotCommandScopeChat(chat_id=admin_id))
    await bot.set_my_commands(commands=user_commands)
    await bot.set_webhook(f"{conf.bot.BASE_WEBHOOK_URL}{conf.bot.WEBHOOK_PATH}")


async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    await bot.delete_my_commands()


async def main_polling():
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


def main_webhook():
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

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path=conf.bot.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=conf.bot.WEB_SERVER_HOST, port=conf.bot.WEB_SERVER_PORT)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    # asyncio.run(main_polling())
    main_webhook()
