from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from db import User, TestAnswer
from utils.keyboard import UserButtons
from utils.services import greeting_user

command_router = Router()


@command_router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await greeting_user(message)


@command_router.message(Command(commands='dasturchi'))
async def dev_command_handler(message: Message) -> None:
    await message.answer(
        '👨🏼‍💻 <a href="https://t.me/sarvar_py_dev">Dasturchi:</a> <a href="https://github.com/sarvar-py-dev">Sarvarbek</a>')


@command_router.message(Command(commands='myinfo'))
async def myinfo_command_handler(message: Message) -> None:
    rkb = ReplyKeyboardBuilder(
        [[KeyboardButton(text=UserButtons.CHANGE_FIRST_NAME), KeyboardButton(text=UserButtons.CHANGE_LAST_NAME)],
         [KeyboardButton(text=UserButtons.BACK)]])
    user = await User.get(message.from_user.id)
    await message.answer(f'''🙎🏻‍♂️ Ism: {user.first_name}
🙎🏻‍♂️ Familiya: {user.last_name}
📞 Telefon raqam: +998{user.phone_number}
📊 Qatnashgan testlar soni: {await TestAnswer.count_by(TestAnswer.user_id == user.id)} ta
Tanlang: 👇''', reply_markup=rkb.as_markup(resize_keyboard=True))


@command_router.message(Command(commands='help'))
async def help_command_handler(message: Message) -> None:
    await message.answer(F'''Buyruqlar:
/start - Siz bu buyruq bilan botni ishga tushirasiz \n
/myinfo - Uzingizning malumotlaringizni yangilaysiz \n
/help - Botning vazifalarini tushinish\n
Tugmalar:
<i>{UserButtons.CHECK_ANSWER}</i> - Botga kiritilgan testlarni javoblarini kiritish\n
<i>{UserButtons.ADMIN}</i> - Admin bilan bog'lanish \n
<i>Agar sizda qandaydir muammo bulsa yoki savollaringiz bulsa <a href='https://t.me/Abdusamatov_Xumoyun'>Admin</a> ga murojat qiling</i>
''')


@command_router.message()
async def any(message: Message):
    await message.answer("""<a href="https://t.me/Eng_Math_Piima_bot">@Eng_Math_Piima_bot</a>

<i>Foydalanish bo'yicha to'liq ma'lumot olish uchun /help buyrug'idan foydalaning</i>""")
