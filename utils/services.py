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
            str(e) + f""" id: <a href='tg://user?id={user_id}'>{user_id}</a> botni block qilgani uchun habar ushbu userga yuborilmadi""")


async def create_statistic_test_answers(test: Test, answers):
    answers_users = await TestAnswer.get_ordered_test_answers(test.id)
    users = ''
    for i, test_answer in enumerate(answers_users, start=1):
        users += f"""<tr>
                <td align='center'> {i}</td>
                <td align='center'>{test_answer.user.last_name} {test_answer.user.first_name}</td>
                <td align='center'>+998 {test_answer.user.phone_number}</td>
                <td align='center'> {len(test_answer.accepted_answers)}</td>
                <td align='center'> {test_answer.quality_level:.1f}%</td>
                <td align='center'> {test_answer.created_at.date()} {test_answer.created_at.hour}:{test_answer.created_at.minute}:{test_answer.created_at.second}</td>
            </tr>"""

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Test hisoboti</title>
    <style>
        table, th, td {
    border: 1px solid black;
            border-collapse: collapse;
        }

        body {
    background-color: rgb(253, 253, 239);
        }

        .body {
    margin: 0 20px 0 10px;
        }
    </style>
""" + f"""<body>
<div class="body">

    </br><b>Ushbu hisobot <a href="https://t.me/{conf.bot.BOT_USERNAME}"><font color='red'>@{conf.bot.BOT_USERNAME}</font></a> orqali
    tayyorlandi.</b></br>

    <b>Test kodi:</b> {test.id} </br>
    <b>Savollar soni:</b> {len(test.answers)} ta </br></br>
    <table width='100%'>
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
    <b>To`g`ri javoblar:</b>
    <br>📝 <b>Kalitlar:</b> {answers} <br><b>Testda qatnashganlarga rahmat...</b>😊😊😊

</div>
</body>
</html>"""
    with open(f"media/test-statistics/{test.id}_natijalar.html", 'w', encoding='utf-8') as file:
        file.write(template)
