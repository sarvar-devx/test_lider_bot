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

        user = await User.get(update.event.from_user.id)
        if not user:
            user = await User.create(id=update.event.from_user.id, username=update.event.from_user.username,
                                     first_name=update.event.from_user.first_name,
                                     last_name=update.event.from_user.last_name)
            message_texts = message.text.split()
            if len(message_texts) == 2 and message.text.startswith('/start') and message_texts[-1].isdigit():
                ref_user = await User.get(int(message_texts[-1]))
                if ref_user:
                    await User.update(user.id, referral_user_id=ref_user.id)
                    if (await User.count_by(User.referral_user_id == ref_user.id)) % 5 == 0:
                        await message.bot.send_message(ref_user.id,
                                                       "🎉 <b>Tabriklaymiz!</b>\n\n👏 Siz 5 ta do'stingizni taklif qilganingiz uchun sizga maxsus bir martalik havola beramiz! 🥳✨")
                        await create_one_time_channel_link(ref_user.id, message.bot)

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
