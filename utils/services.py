from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from db import TestAnswer, Test
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


async def create_statistic_test_answers(test: Test, answers):
    answers_users = await TestAnswer.get_ordered_test_answers(test.id)
    users = ''
    for i, test_answer in enumerate(answers_users, start=1):
        users += f"""<tr>
                <td align='center'> {i}</td>d
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
    background - color: rgb(253, 253, 239);
        }

        .body {
    margin: 0 20px 0 10px;
        }
    </style>
""" + f"""<body>
<div class="body">

    </br><b>Ushbu hisobot <a href="https://t.me/Eng_Math_Piima_bot"><font color='red'>@Eng_Math_Piima_bot</font></a> orqali
    tayyorlandi.</b></br>
    <b>Test muallifi:</b> Xumoyun Abdusamatov <br>

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
