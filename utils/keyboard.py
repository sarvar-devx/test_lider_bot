from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from aiogram.utils.keyboard import ReplyKeyboardBuilder


class UserButtons:
    CHECK_ANSWER = '✅ Javobni tekshirish'
    ADMIN = '👨‍💼 Admin'
    CHANGE_FIRST_NAME = "✍ Ismni o'zgartirish"
    CHANGE_LAST_NAME = "✍ Familiyani o'zgartirish"
    BACK = '🔙 Orqaga'


class AdminButtons:
    CREATE_TEST = '✍ Test Yaratish'
    STATISTIC = '📊 Testlar Statistikasi'
    TO_ANNOUNCE = '📣 Kanallarga elon berish'
    SKIP = "⏭️ O'tkazib yuborish"


def main_keyboard_btn(**kwargs):
    main_keyboard = ReplyKeyboardBuilder()
    main_keyboard.row(KeyboardButton(text=UserButtons.CHECK_ANSWER, **kwargs))
    main_keyboard.row(KeyboardButton(text=UserButtons.ADMIN, **kwargs))
    main_keyboard.adjust(2, repeat=True)
    return main_keyboard


def admin_keyboard_btn(**kwargs):
    keyboard_btn = ReplyKeyboardBuilder()
    keyboard_btn.row(KeyboardButton(text=AdminButtons.CREATE_TEST, **kwargs))
    keyboard_btn.row(KeyboardButton(text=AdminButtons.STATISTIC, **kwargs))
    keyboard_btn.row(KeyboardButton(text=AdminButtons.TO_ANNOUNCE, **kwargs))
    keyboard_btn.adjust(2, repeat=True)
    return keyboard_btn


phone_number_rkb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='📞 Telefon raqamni yuborish', request_contact=True)]], resize_keyboard=True)

skip_cancel_rkb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=AdminButtons.SKIP)], [KeyboardButton(text=UserButtons.BACK)]], resize_keyboard=True)


