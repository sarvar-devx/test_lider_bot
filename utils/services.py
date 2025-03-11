from typing import Callable

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, ChatInviteLink

from config import conf
from db import TestAnswer, Test, ReferralMessage
from utils.keyboard import main_keyboard_btn
from utils.states import UserStates, CreateTestStates, CheckTestAnswersStates


async def greeting_user(message: Message):
    await message.answer(
        f"<b>👋 Assalomu alaykum <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a>, botimizga xush kelibsiz.</b>",
        reply_markup=main_keyboard_btn().as_markup(resize_keyboard=True))


async def wrong_first_last_name(message: Message) -> None:
    await message.answer('<b>🙅 Ism yoki Familiyada faqat harflardan iboorat</b>')


async def send_first_name(message: Message, state: FSMContext) -> None:
    await message.answer("✍️ <b>Ismingizni kiriting</b>", reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserStates.first_name)


async def send_last_name(message: Message, state: FSMContext) -> None:
    await message.answer('✍ <b>Familiyangizni kiriting.</b>')
    await state.set_state(UserStates.last_name)


async def validate_name_input(message: Message, retry_function: Callable, state: FSMContext = None) -> bool:
    if not message.text or not message.text.isalpha():
        await wrong_first_last_name(message)
        await retry_function(message, state)
        return False
    return True


async def create_test_send_answers(message: Message, state: FSMContext) -> None:
    await message.answer('Test ❕Javoblarini kiriting \nMasalan: abcd... yoki 1a2b3c4d...')
    await state.set_state(CreateTestStates.answers)


async def create_test_answers_send_user_answers(message: Message, state: FSMContext, sending_text: str) -> None:
    await message.answer(sending_text + "\n<blockquote>Format: abcd... yoki 1a2b3c4d...</blockquote>")
    await state.set_state(CheckTestAnswersStates.user_answers)


async def create_one_time_channel_link(user_id: int, bot: Bot) -> None:
    invite_link: ChatInviteLink = await bot.create_chat_invite_link(
        chat_id=conf.bot.OLYMPIAD_CHANNEL_ID,
        expire_date=None,
        member_limit=1
    )
    await bot.send_message(user_id,
                           f"""🔗 <b>Siz uchun maxsus OLIMPIADA boʻladigan kanal uchun bir martalik taklif havolasi!</b>\n
🎉 <b>Havola:</b> <a href='{invite_link.invite_link}'>👉 Bu yerni bosing</a>\n
❗ <i>Diqqat:</i> Ushbu havola faqat <b>bir marta</b> ishlatilishi mumkin.
⏳ Uni boshqa birovdan oldin ishlatishni unutmang!""")


async def referral_user(message: Message, user_id) -> None:
    data: ReferralMessage = (await ReferralMessage.all())[0]
    try:
        await message.bot.send_photo(user_id, data.photo,
                                     caption=data.description + f"""\n\n👉🏻 <a href="https://t.me/{conf.bot.BOT_USERNAME}?start={user_id}">Havola ustiga bosing</a> 👈🏻
👉🏻 <a href="https://t.me/{conf.bot.BOT_USERNAME}?start={user_id}">Havola ustiga bosing</a> 👈🏻
👉🏻 <a href="https://t.me/{conf.bot.BOT_USERNAME}?start={user_id}">Havola ustiga bosing</a> 👈🏻""")
        await message.bot.send_message(user_id, """🔝 <b>YUQORIDAGI POSTNI</b> do'stlaringizga yuboring.

<u><b>5 ta</b></u> do'stingiz sizning taklif havolingiz orqali <b>BOTga</b> kirib, kanallarga a'zo bo'lib, ro'yxatdan o'tsa, bot sizga <b>OLIMPIADA boʻladigan kanal</b> uchun bir martalik link beradi.""")
    except TelegramForbiddenError as e:
        await message.answer(
            f"""{e} id: <a href='tg://user?id={user_id}'>{user_id}</a> botni block qilgani uchun habar ushbu foydalanuvchiga yuborilmadi""")


async def create_statistic_test_answers(test: Test, answers):
    answers_users = await TestAnswer.get_ordered_test_answers(test.id)
    users = ''
    for i, test_answer in enumerate(answers_users, start=1):
        users += f"""<tr>
                <td> {i}</td>
                <td>{test_answer.user.last_name} {test_answer.user.first_name}</td>
                <td>+998 {test_answer.user.phone_number}</td>
                <td> {len(test_answer.accepted_answers)}</td>
                <td> {test_answer.quality_level:.1f}%</td>
                <td> {test_answer.created_at.date()} {test_answer.created_at.hour}:{test_answer.created_at.minute}:{test_answer.created_at.second}</td>
            </tr>"""

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Test hisoboti</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #e3f2fd;
            color: #333;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 90%;
            width: 950px;
            margin: auto;
            background: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
        }

        h2 {
            text-align: center;
            color: #007bff;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: center;
        }

        th {
            background: #64b5f6;
            color: white;
        }

        tr:nth-child(even) {
            background: #c6e4ff;
        }

        tr:hover {
            background: #9ddaff;
            color: #697268;
        }

        .highlight {
            color: red;
            font-weight: bold;
        }

        .footer {
            text-align: center;
            margin-top: 20px;
            font-size: 14px;
            background: #64b5f4;
            color: #000000;
            padding: 10px;
            border-radius: 8px;
        }

        a {
            color: #ff4081;
            text-decoration: none;
            font-weight: bold;
        }

        a:hover {
            text-decoration: underline;
        }
    </style>
""" + f"""<body>
<div class="container">
    <h2>📊 Test Hisoboti</h2>
    <p><b>Ushbu hisobot <a href="https://t.me/{conf.bot.BOT_USERNAME}"><font color='red'>@{conf.bot.BOT_USERNAME}</font></a> orqali tayyorlandi.</b>
    </p>
    <p><b>Test muallifi:</b> Xumoyun Abdusamatov</p>
    <p><b>Test kodi:</b> {test.id}</p>
    <p><b>Savollar soni:</b> {len(test.answers)} ta</p>
    
    <table>
        <thead>
        <tr style='background-color:beige;'>
            <th>T/r</th>
            <th>Ism Familiya</th>
            <th>Telefon raqam</th>
            <th>Natija</th>
            <th>Foiz</th>
            <th>Vaqti</th>
        </tr>
        </thead>
        <tbody>

        {users}


        </tbody>
    </table>
    <br>
    <div class="footer">
        <p><b>✅ To'g'ri javoblar:</b></p>
        <p>📝 <b>Kalitlar:</b> {answers}</p>
        <p><b>Testda qatnashganlarga rahmat!</b> 😊😊😊</p>
    </div>
</div>
</body>
</html>"""
    with open(f"media/test-statistics/{test.id}_natijalar.html", 'w', encoding='utf-8') as file:
        file.write(template)
