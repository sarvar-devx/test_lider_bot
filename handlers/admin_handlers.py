import re

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, CallbackQuery, \
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile, document
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import conf
from db import Test, TestAnswer, User
from utils.create_certificates import sending_certificates
from utils.filters import IsAdminFilter
from utils.keyboard import admin_keyboard_btn, AdminButtons, UserButtons
from utils.middlware import make_channels_button
from utils.services import create_test_send_answers, create_statistic_test_answers
from utils.states import NewsStates, CreateTestStates

admin_router = Router()
admin_router.message.filter(IsAdminFilter())
admin_router.callback_query.filter(IsAdminFilter())


@admin_router.message(F.text == UserButtons.BACK)
async def back_admin_menu_handler(message: Message, state: FSMContext):
    await command_start_handler(message, state)


@admin_router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await message.answer('Siz adminsiz menuni tanlang',
                         reply_markup=admin_keyboard_btn().as_markup(resize_keyboard=True),
                         parse_mode=ParseMode.MARKDOWN)
    await state.clear()


@admin_router.message(F.text == AdminButtons.TO_ANNOUNCE)
async def news_handler(message: Message, state: FSMContext) -> None:
    await message.answer('Elonni Kiriting', reply_markup=ReplyKeyboardRemove())
    await state.set_state(NewsStates.news)


@admin_router.message(NewsStates.news)
async def confirm_handler(message: Message, state: FSMContext) -> None:
    ikb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='✅ Ha', callback_data='confirm_news_' + str(message.message_id)),
                          InlineKeyboardButton(text="❌ Yo'q", callback_data='dont_confirm')]])
    await message.answer('Bu elonni tasdiqlaysizmi', reply_markup=ikb, reply_to_message_id=message.message_id)
    await state.clear()


@admin_router.callback_query(F.data.startswith('confirm_news'))
async def send_news_handler(callback: CallbackQuery, state: FSMContext) -> None:
    message_id = callback.data.split('_')[-1]
    for channel in conf.bot.CHANNELS:
        await callback.bot.copy_message(chat_id=channel, from_chat_id=callback.message.chat.id,
                                        message_id=int(message_id))
    await callback.message.edit_reply_markup()
    ikb = await make_channels_button(conf.bot.CHANNELS, callback.bot)
    await callback.message.answer('Elonlar shu chanellarga tashlandi', reply_markup=ikb.as_markup())
    await command_start_handler(callback.message, state)


@admin_router.callback_query(F.data.startswith('dont_confirm'))
async def dont_send_news_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await command_start_handler(callback.message, state)


@admin_router.message(F.text == AdminButtons.CREATE_TEST)
async def create_test_handler(message: Message, state: FSMContext) -> None:
    await message.answer('Test nomini kiriting',
                         reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=UserButtons.BACK)]],
                                                          resize_keyboard=True))
    await state.set_state(CreateTestStates.name)


@admin_router.message(CreateTestStates.name)
async def create_test_send_answers_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await create_test_send_answers(message, state)


@admin_router.message(CreateTestStates.answers)
async def create_test_handler(message: Message, state: FSMContext) -> None:
    try:
        answers = {}
        if not message.text.isalnum():
            raise ValueError
        if message.text.isalpha():
            for index, value in enumerate(message.text, 1):
                answers[str(index)] = value.lower()
        else:
            numbers = 0
            letters = 0
            for i in range(len(message.text) - 1):
                if message.text[i].isdigit() and message.text[i + 1].isdigit():
                    continue
                if message.text[i].isdigit():
                    numbers += 1
                elif message.text[i].isalpha():
                    letters += 1
            if message.text[-1].isdigit():
                numbers += 1
            elif message.text[-1].isalpha():
                letters += 1
            if numbers != letters:
                raise ValueError
            letters = re.findall(r"[a-zA-Z]", message.text)
            for index, value in enumerate(letters, 1):
                answers[str(index)] = value.lower()

    except ValueError:
        await message.answer("Siz kiritgan javoblar formati noto'g'ri, iltimos tekshirib so'ralgan formatda yuboring.")
        await create_test_send_answers(message, state)
        return

    await state.update_data(answers=answers)
    ikb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='✅ Ha', callback_data='confirm_creating_test'),
                          InlineKeyboardButton(text="❌ Yo'q", callback_data='dont_create')]])
    test = await state.get_data()
    answers = ''
    for k, v in test['answers'].items():
        answers += F"<tg-spoiler><b>{k}: {v}</b></tg-spoiler>,  "
    await message.answer(f"""
✍ Test nomi: {test['name']}
❓ Savollar soni: {len(test['answers'])}
🔐 To'g'ri javoblar: {answers}\n
📥 Tasdiqlaysizmi """, reply_markup=ikb)


@admin_router.callback_query(F.data.startswith('confirm_creating_test'))
async def confirm_creating_test_handler(callback: CallbackQuery, state: FSMContext) -> None:
    test = await state.get_data()
    if test.get('name') is None:
        await callback.message.delete()
        await callback.message.answer('❌ Testni yaratib bulmaydi chunki testni o\'z vaqtida qilish kerak edi')
        await command_start_handler(callback.message, state)
        return

    created_test = await Test.create(**test)
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        f"✅ Test bazaga qo'shildi.\n#⃣ Test kodi: <code>{created_test.id}</code>\n📆Yaratilgan vaqt: 📅 {created_test.created_at.date()} 🕰 {created_test.created_at.hour}:{created_test.created_at.minute}")
    await command_start_handler(callback.message, state)


@admin_router.callback_query(F.data.startswith('dont_create'))
async def dont_create_test_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer('❌ Test Yaratilmadi')
    await command_start_handler(callback.message, state)


@admin_router.callback_query(F.data.startswith('test_statistics'))
async def test_statistics_handler(callback: CallbackQuery):
    test = await Test.get(int(callback.data.split('_')[-1]))
    answers = ""
    for k, v in test.answers.items():
        answers += f"{k}-{v.upper()},"

    if test.is_active:
        await create_statistic_test_answers(test, answers)
    await callback.bot.send_document(
        chat_id=callback.from_user.id,
        document=FSInputFile(f'media/test-statistics/{test.id}_natijalar.html'),
        caption=f"""<b>✍️ Hisobot!</b>
📌 <b>Test kodi:</b> {test.id}
👨 <b>Qatnashchilar soni</b>: {await TestAnswer.count_by(TestAnswer.test_id == test.id)} ta
📝 <b>Kalitlar:</b> {answers}""")


@admin_router.callback_query(F.data.startswith('stop_test'))
async def stop_test_handler(callback: CallbackQuery):
    test = await Test.get(int(callback.data.split('_')[-1]))
    if not test.is_active:
        await callback.answer('❌ Test allaqachon yakunlangan')
        return

    await test.update(test.id, is_active=False)

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data='certificate_id_1__test_id_' + str(test.id)),
         InlineKeyboardButton(text="2", callback_data='certificate_id_2__test_id_' + str(test.id)),
         InlineKeyboardButton(text="3", callback_data='certificate_id_3__test_id_' + str(test.id)),
         InlineKeyboardButton(text="4", callback_data='certificate_id_4__test_id_' + str(test.id))]
    ])
    await callback.bot.send_photo(callback.from_user.id, FSInputFile('media/certificate_types/certificates.png'),
                                  caption="🏆 Certificateni tanlang",
                                  reply_markup=ikb)


@admin_router.callback_query(F.data.startswith('certificate_id_'))
async def sending_certificates_handler(callback: CallbackQuery):
    data = callback.data.split('__')
    certificate_id = int(data[0][-1])
    test = await Test.get(int(data[-1][-1]))
    await callback.message.edit_reply_markup()
    await callback.answer('🏆 Certificatelar tarqatilmoqda', show_alert=True)
    await sending_certificates(callback.bot, test, certificate_id)
    answers = ""
    for k, v in test.answers.items():
        answers += f"{k}-{v.upper()},"
    await create_statistic_test_answers(test, answers)
    await callback.message.answer('🏆 Certificatelar tarqatildi')
    await callback.bot.send_document(callback.from_user.id,
                                     FSInputFile(f"media/test-statistics/{test.id}_natijalar.html"),
                                     caption=f"""💡 <b>Test yakunlandi!
📝 Test nomi: {test.name}
🔰 Test kodi</b>: {test.id}
👨 <b>Test qatnashchilari</b>: {await TestAnswer.count_by(TestAnswer.test_id == test.id)} ta
 <b>Kalitlar</b>: {answers}""")


@admin_router.message(F.text == AdminButtons.STATISTIC)
async def statistics_handler(message: Message):
    tests = await Test.all()
    ikb = InlineKeyboardBuilder()
    for test in tests:
        ikb.row(InlineKeyboardButton(text=test.name, callback_data="test_id" + str(test.id)))
    ikb.adjust(2)
    await message.answer('Testlar', reply_markup=ikb.as_markup())


@admin_router.callback_query(F.data.startswith('test_id'))
async def tests_handler(callback: CallbackQuery):
    test = await Test.get(int(callback.data.split('test_id')[-1]))
    answers = ""
    for k, v in test.answers.items():
        answers += f"{k}-{v.upper()},"
    text = f"""💡 <b>📝 Test nomi: {test.name}
🔰 Test kodi</b>: {test.id}
👨 <b>Test qatnashchilari</b>: {await TestAnswer.count_by(TestAnswer.test_id == test.id)} ta
🔑<b>Kalitlar</b>: {answers}"""

    if not test.is_active:
        text += "\n❌ Test yakunlangan"
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Holat", callback_data='test_statistics_' + str(test.id))]])
    else:
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Holat", callback_data='test_statistics_' + str(test.id)),
             InlineKeyboardButton(text='⏰ Yakunlash', callback_data='stop_test_' + str(test.id))]])
    await callback.message.answer(text, reply_markup=ikb)


@admin_router.message(F.text == AdminButtons.USERS)
async def send_users_info(message: Message):
    users = await User.all()
    admins = await User.filter(User.id.in_(conf.bot.get_admin_list))
    admins_str = ""
    for i, admin in enumerate(admins, 1):
        admins_str += f"""<tr>
            <td align="center"> {i}</td>
            <td align="center"><a href='{f"tg://user?id={admin.id}" if admin.username is None else f"https://t.me/{admin.username}"}'>{"Username mavjud emas" if admin.username is None else admin.username}</a></td>
            <td align="center">{admin.first_name}{admin.last_name}</td>
            <td align="center"><a href="tel:+998{admin.phone_number}">+998{admin.phone_number}</a></td>
            <td align="center"> {admin.created_at.date()}</td>
        </tr>"""
    user_str = ""
    for i, user in enumerate(users, 1):
        user_str += f"""<tr>
            <td align="center"> {i}</td>
            <td align="center"><a href='{f"tg://user?id={user.id}" if user.username is None else f"https://t.me/{user.username}"}'>{"Username mavjud emas" if user.username is None else user.username}</a></td>
            <td align="center">{user.last_name}{user.first_name}</td>
            <td align="center"><a href="tel:+998{user.phone_number}">+998{user.phone_number}</a></td>
            <td align="center"> {user.created_at.date()}</td>
        </tr>"""
    message_text = """ 
<!DOCTYPE html>
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
</head>"""
    message_text += f"""<body>
<div class="body">
    <br>
    <b> Adminlar: </b> {len(admins)} ta
    <br>
    <br>
    <table width="100%">
        <thead>
        <tr style="background-color:limegreen;">
            <th>T/r</th>
            <th>Username</th>
            <th>Ism Familiya</th>
            <th>Telefon raqam</th>
            <th>Botga register qilgan vaqti</th>
        </tr>
        </thead>
        <tbody>
        {admins_str}
        </tbody>
    </table>
    <br>
    <br>
    <br>
    <b>Hamma Foydalanuvcholar:</b> {len(users)} ta
    <br>
    <br>
    <table width="100%">
        <thead>
        <tr style="background-color:yellow;">
            <th>T/r</th>
            <th>Username</th>
            <th>Ism Familiya</th>
            <th>Telefon raqam</th>
            <th>Botga register qilgan vaqti</th>
        </tr>
        </thead>
        <tbody>
        {user_str}
        </tbody>
    </table>
</div>
</body>
</html>
"""

    with open(f"media/users_list_for_admin.html", 'w', encoding='utf-8') as file:
        file.write(message_text)

    await message.answer_document(FSInputFile('media/users_list_for_admin.html'))
