import re

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, CallbackQuery, \
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func

from config import conf
from db import Test, TestAnswer, User
from db.base import db
from db.models import ReferralMessage
from utils.create_certificates import sending_certificates
from utils.filters import IsAdminFilter
from utils.keyboard import admin_keyboard_btn, AdminButtons, UserButtons
from utils.middlware import make_channels_button
from utils.services import create_test_send_answers, create_statistic_test_answers, referral_user, \
    create_one_time_channel_link
from utils.states import NewsStates, CreateTestStates, CreateReferralStyleStates, NotificationStates

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


@admin_router.message(Command(commands='elon'))
async def elon_command_handler(message: Message, state: FSMContext) -> None:
    await message.answer('Elonni Kiriting', reply_markup=ReplyKeyboardRemove())
    await state.set_state(NotificationStates.notification)


@admin_router.message(NotificationStates.notification)
async def notification_handler(message: Message, state: FSMContext) -> None:
    ikb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='✅ Ha', callback_data=f'confirm_notification_{message.message_id}'),
                          InlineKeyboardButton(text="❌ Yo'q", callback_data='dont_confirm')]])
    await message.reply("Bu elonni tasdiqlaysizmi", reply_markup=ikb)
    await state.clear()


@admin_router.callback_query(F.data.startswith('confirm_notification'))
async def confirm_notification_handler(callback: CallbackQuery, state: FSMContext) -> None:
    message_id = callback.data.split('_')[-1]
    users = await User.all()
    for user in users:
        try:
            await callback.bot.copy_message(chat_id=user.id, from_chat_id=callback.message.chat.id,
                                            message_id=int(message_id))
        except TelegramForbiddenError as e:
            await callback.message.answer(
                f"""{e} id: <a href='tg://user?id={user.id}'>{user.id}</a> botni block qilgani uchun habar ushbu foydalanuvchiga yuborilmadi""")

    await callback.message.edit_reply_markup()
    await callback.message.answer("Elon barcha foydalanuvchilarga tarqatildi")
    await command_start_handler(callback.message, state)


@admin_router.message(Command(commands='to_announce'))
async def news_command_handler(message: Message, state: FSMContext) -> None:
    await message.answer('Elonni Kiriting', reply_markup=ReplyKeyboardRemove())
    await state.set_state(NewsStates.news)


@admin_router.message(NewsStates.news)
async def confirm_news_handler(message: Message, state: FSMContext) -> None:
    ikb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='✅ Ha', callback_data=f'confirm_news_{message.message_id}'),
                          InlineKeyboardButton(text="❌ Yo'q", callback_data='dont_confirm')]])
    await message.reply('Bu elonni tasdiqlaysizmi', reply_markup=ikb)
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
    await callback.answer('Bekor qilindi ❌')
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
    await callback.answer('❌ Jarayon tasdiqlanmadi va yaratilmadi', show_alert=True)
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

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data=f'certificate_id_1__test_id_{test.id}'),
         InlineKeyboardButton(text="2", callback_data=f'certificate_id_2__test_id_{test.id}'),
         InlineKeyboardButton(text="3", callback_data=f'certificate_id_3__test_id_{test.id}'),
         InlineKeyboardButton(text="4", callback_data=f'certificate_id_4__test_id_{test.id}')]
    ])
    await callback.bot.send_photo(callback.from_user.id, FSInputFile('media/certificate_types/certificates.png'),
                                  caption="🏆 Certificateni tanlang",
                                  reply_markup=ikb)


@admin_router.callback_query(F.data.startswith('certificate_id_'))
async def sending_certificates_handler(callback: CallbackQuery):
    data = callback.data.split('__')
    certificate_id = int(data[0].split("_")[-1])
    test = await Test.get(int(data[-1].split("_")[-1]))
    if not test.is_active:
        await callback.answer('❌ Test allaqachon yakunlangan')
        return
    await test.update(test.id, is_active=False)
    await callback.message.edit_reply_markup()
    await callback.answer('🏆 Certificatelar tarqatilmoqda', show_alert=True)
    await sending_certificates(callback.bot, test, certificate_id)
    answers = ""
    for k, v in test.answers.items():
        answers += f"{k}-{v.upper()},"
    await create_statistic_test_answers(test, answers)
    for admin_id in conf.bot.get_admin_list:
        await callback.bot.send_message(admin_id, '🏆 Certificatelar tarqatildi')
        await callback.bot.send_document(admin_id,
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
        ikb.row(InlineKeyboardButton(text=test.name, callback_data=f"test_id{test.id}"))
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
            [InlineKeyboardButton(text="📊 Holat", callback_data=f'test_statistics_{test.id}')]])
    else:
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Holat", callback_data=f'test_statistics_{test.id}'),
             InlineKeyboardButton(text='⏰ Yakunlash', callback_data=f'stop_test_{test.id}')]])
    await callback.message.answer(text, reply_markup=ikb)


@admin_router.message(F.text == AdminButtons.REFERRAL_USER_STYLE)
async def referral_user_style_handler(message: Message, state: FSMContext):
    await message.answer(
        'Referral userni qanday yuborish kerak rasmni 🖼 kiriting!!!',
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=UserButtons.BACK)]],
                                         resize_keyboard=True))
    await state.set_state(CreateReferralStyleStates.photo)


@admin_router.message(CreateReferralStyleStates.photo)
async def referral_style_photo_handler(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer('Nimadir hato ketdi qaytadan urinib ko\'ring')
        await referral_user_style_handler(message, state)
        return
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer('Endi esa tavsifini kiriting 🗒')
    await state.set_state(CreateReferralStyleStates.description)


@admin_router.message(CreateReferralStyleStates.description)
async def referral_style_message_handler(message: Message, state: FSMContext):
    await state.update_data(description=message.html_text)
    ikb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='✅ Ha', callback_data='confirm_creating_referral_style'),
                          InlineKeyboardButton(text="❌ Yo'q", callback_data='dont_create')]])
    data = await state.get_data()
    await message.bot.send_photo(message.chat.id, data['photo'], caption=data[
                                                                             'description'] + f"""\n\n👉🏻 <a href="https://t.me/{conf.bot.BOT_USERNAME}?start={message.from_user.id}">Havola ustiga bosing</a> 👈🏻
👉🏻 <a href="https://t.me/{conf.bot.BOT_USERNAME}?start={message.from_user.id}">Havola ustiga bosing</a> 👈🏻
👉🏻 <a href="https://t.me/{conf.bot.BOT_USERNAME}?start={message.from_user.id}">Havola ustiga bosing</a> 👈🏻""" + "\n\n\n Tasdiqlaysizmi",
                                 reply_markup=ikb)


@admin_router.callback_query(F.data.startswith('confirm_creating_referral_style'))
async def create_referral_style_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('photo') is None or data.get('description') is None:
        await callback.answer('❌ Jarayon amalga oshmadi, bu o\'z vaqtida tasdiqlanmagan', show_alert=True)
        await callback.message.delete()
        await command_start_handler(callback.message, state)
        return

    if referral_messages := await ReferralMessage.all():
        await ReferralMessage.delete(referral_messages[0].id)
    await ReferralMessage.create(**data)
    await callback.message.edit_reply_markup()
    await callback.answer('tasdiqlandi ✅', show_alert=True)
    await command_start_handler(callback.message, state)


@admin_router.message(F.text == AdminButtons.REFERRAL_USER)
async def referral_user_admin_handler(message: Message):
    users = await User.all()
    for user in users:
        await referral_user(message, user.id)
    await message.answer("Barcha userlarga odam yig'ishi uchun link tarqatildi")


@admin_router.message(F.text == AdminButtons.OLYMPIAD_CHANNEL_BUTTON)
async def one_time_link_handler(message: Message, bot: Bot):
    await create_one_time_channel_link(message.from_user.id, bot)


@admin_router.message(Command(commands='users_stats'))
async def users_stats_handler(message: Message) -> None:
    users = await User.all()
    users_str = ""
    for i, user in enumerate(users, 1):
        user_link = f"tg://user?id={user.id}" if user.username is None else f"https://t.me/{user.username}"
        username = "Username mavjud emas" if user.username is None else user.username
        referrer = "<del>Mavjud emas</del>"
        if user.referrer_id:
            referrer_link = f"tg://user?id={user.referrer_id}" if user.referrer.username is None else f"https://t.me/{user.referrer.username}"
            referrer = f'{user.referrer_id} (<a class="username" href="{referrer_link}">{user.referrer.first_name}</a>)'
        counter = sum(1 for user_ in users if user_.referrer_id == user.id)
        users_str += f"""<div class="user-item">
            <span class="username">{i}. <a class="username" href="{user_link}">{username}</a></span><br>
            <span class="stats">Ism: {user.first_name} <b style="color: black">|</b> </span>
            <span class="stats">Familiya: {user.last_name if user.last_name else "<del>Mavjud emas</del>"}</span><br>
            <span class="stats">Telefon: <a href="tel:+998{user.phone_number}">+998{user.phone_number}</a></span><br>
            <span class="stats">Referral ID: {referrer}</span><br>
            <span class="stats">Taklif qilinganlar: {counter}</span>
        </div>"""

    message_text = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Foydalanuvchilar Statistikasi</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #e0e5ec;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            max-width: 1000px;
            width: 100%;
            background: #e0e5ec;
            padding: 30px;
            border-radius: 20px;
            box-shadow: inset 5px 5px 15px #babecc, inset -5px -5px 15px #ffffff;
        }

        h2 {
            text-align: center;
            color: #333;
        }

        .user-list {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
            padding: 0;
        }

        .user-item {
            background: #e0e5ec;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 7px 7px 15px #babecc, -7px -7px 15px #ffffff;
            width: 300px;
            text-align: center;
            transition: all 0.3s ease;
        }

        .user-item:hover {
            box-shadow: inset 7px 7px 15px #babecc, inset -7px -7px 15px #ffffff;
        }

        .username {
            font-weight: bold;
            color: #007bff;
            font-size: 20px;
        }

        .stats {
            color: #555;
            font-size: 16px;
        }
    </style>
</head>""" + f"""<body>
<div class="container">
    <h2>Foydalanuvchilar Statistikasi</h2>
    <div class="user-list">
        {users_str}
    </div>
</div>
</body>
</html>
"""
    with open(f"media/users_stats.html", 'w', encoding='utf-8') as file:
        file.write(message_text)

    await message.answer_document(FSInputFile('media/users_stats.html'))


async def get_users_test_counts(user_ids):
    query = (
        select(TestAnswer.user_id, func.count().label("test_count"))
        .where(TestAnswer.user_id.in_(user_ids))
        .group_by(TestAnswer.user_id)
    )
    result = await db.execute(query)
    return {row.user_id: row.test_count for row in result.all()}


async def generate_user_table(users):
    rows = []
    user_ids = [user.id for user in users]
    test_counts = await get_users_test_counts(user_ids)

    for i, user in enumerate(users, 1):
        user_link = f"tg://user?id={user.id}" if user.username is None else f"https://t.me/{user.username}"
        username = "Username mavjud emas" if user.username is None else user.username
        rows.append(f"""<tr>
            <td>{i}</td>
            <td><a href='{user_link}'>{username}</a></td>
            <td>{user.first_name}</br> {user.last_name if user.last_name else "<del>Familiyasi yo'q</del>"}</td>
            <td><a href="tel:+998{user.phone_number}">+998{user.phone_number}</a></td>
            <td>{user.created_at.date()}</td>
            <td>{test_counts.get(user.id, 0)}</td>
        </tr>""")
    return "\n".join(rows)


@admin_router.message(F.text == AdminButtons.USERS)
async def send_users_info(message: Message):
    users = await User.all()
    admins = [user for user in users if user.id in conf.bot.get_admin_list]

    admins_str = await generate_user_table(admins)
    user_str = await generate_user_table(users)
    message_text = """ 
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Test hisoboti</title>
    <style>
        body {
            background-color: rgb(253, 253, 239);
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }

        .body {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border: 2px solid #ccc;
        }

        h2 {
            text-align: center;
            color: #333;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        th, td {
            border: 2px solid black;
            padding: 8px;
            text-align: center;
        }

        th {
            background-color: limegreen;
            color: white;
        }

        .yellow th {
            background-color: yellow;
            color: black;
        }

        a {
            text-decoration: none;
            color: #007bff;
        }

        a:hover {
            text-decoration: underline;
        }
    </style>
</head>""" + f"""<body>
<div class="body">
    <h2>Adminlar</h2>
    <p><b>Adminlar:</b> {len(admins)} ta</p>

    <table>
        <thead>
        <tr>
            <th>T/r</th>
            <th>Username</th>
            <th>Ism Familiya</th>
            <th>Telefon raqam</th>
            <th>A’zo bo‘lgan vaqti</th>
            <th>Testlar soni</th>
        </tr>
        </thead>
        <tbody>
        {admins_str}
        </tbody>
    </table>
    
    <h2>Hamma Foydalanuvchilar</h2>
    <p><b>Hamma Foydalanuvchilar:</b> {len(users)} ta</p>
    
    <table class="yellow">
        <thead>
        <tr>
            <th>T/r</th>
            <th>Username</th>
            <th>Ism Familiya</th>
            <th>Telefon raqam</th>
            <th>A’zo bo‘lgan vaqti</th>
            <th>Testlar soni</th>
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

    with open(f"media/users_list.html", 'w', encoding='utf-8') as file:
        file.write(message_text)

    await message.answer_document(FSInputFile('media/users_list.html'))
