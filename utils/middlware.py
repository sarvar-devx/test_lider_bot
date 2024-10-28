from typing import Iterable

from aiogram import BaseMiddleware, Bot
from aiogram.enums import ChatMemberStatus
from aiogram.types import InlineKeyboardButton, Message
from aiogram.types.update import Update
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import conf
from db import User
from utils.services import send_first_name


async def make_channels_button(channel_ids: Iterable, bot: Bot):
    ikb = InlineKeyboardBuilder()
    for i, channel_id in enumerate(channel_ids, 1):
        channel = await bot.get_chat(channel_id)
        ikb.row(
            InlineKeyboardButton(text=f'{i}-Kanal', url=channel.invite_link))
    return ikb


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, update: Update, data):
        message = update.event
        if type(message) is not Message:
            message = message.message
        unsubscribe_channels = [channel_id for channel_id in conf.bot.CHANNELS if (
            await update.bot.get_chat_member(channel_id, update.event.from_user.id)).status == ChatMemberStatus.LEFT]
        if unsubscribe_channels:
            ikb = await make_channels_button(unsubscribe_channels, update.bot)
            ikb.row(InlineKeyboardButton(text='✅ Tasdiqlash',
                                         callback_data='channel_confirm__' + str(message.message_id)))
            await message.answer("Botni foydalanishdan oldin kannalarga a'zo bo'ling",
                                      reply_markup=ikb.as_markup())
            return

        user = await User.get(update.event.from_user.id)
        if not user and not await data['state'].get_state():
            await send_first_name(message, data['state'])
            return

        return await handler(update, data)
