import re

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

from config import conf
from db import User, Test, TestAnswer
from handlers.admin_handlers import back_admin_menu_handler
from handlers.command_handlers import myinfo_command_handler
from utils.keyboard import main_keyboard_btn, phone_number_rkb, UserButtons
from utils.services import greeting_user, wrong_first_last_name, send_last_name, send_first_name, \
    create_test_answers_send_user_answers
from utils.states import UserStates, ChangeLastNameStates, ChangeFirstNameStates, CheckTestAnswersStates

main_router = Router()


@main_router.message(F.text == UserButtons.BACK)
async def back_menu_handler(message: Message, state: FSMContext):
    await message.answer('<b>Bosh Sahifa</b>', reply_markup=main_keyboard_btn().as_markup(resize_keyboard=True))
    await state.clear()


@main_router.message(UserStates.first_name)
async def first_name_handler(message: Message, state: FSMContext) -> None:
    if not message.text.isalpha():
        await wrong_first_last_name(message)
        await send_first_name(message, state)
        return

    await send_last_name(message, state)
    await state.update_data(first_name=message.text)


@main_router.message(UserStates.last_name)
async def last_name_handler(message: Message, state: FSMContext) -> None:
    if not message.text.isalpha():
        await wrong_first_last_name(message)
        await send_last_name(message, state)
        return

    await state.update_data(last_name=message.text)
    await message.answer('📞 <b>Telefon raqamingizni yuboring.</b>', reply_markup=phone_number_rkb)
    await state.set_state(UserStates.phone_number)


@main_router.message(UserStates.phone_number)
async def phone_number_handler(message: Message, state: FSMContext) -> None:
    if message.contact is None:
        await message.answer("<b>🙅 Telefon raqamni pastdagi tugma orqali yuboring 👇</b>", reply_markup=phone_number_rkb)
        return
    phone_number = message.contact.phone_number[-9:]
    user_data = await state.get_data()
    user_data.update({
        'id': message.from_user.id,
        'username': message.from_user.username,
        'phone_number': phone_number,
    })
    await User.create(**user_data)
    if message.from_user.id in conf.bot.get_admin_list:
        await back_admin_menu_handler(message, state)
        return
    await greeting_user(message)
    await state.clear()


@main_router.callback_query(F.data.startswith('channel_confirm'))
async def check_messages(callback_query: CallbackQuery, bot: Bot):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await callback_query.message.answer('✅ Tasdiqlandi\nTanlang👇',
                                        reply_markup=main_keyboard_btn().as_markup(resize_keyboard=True))


@main_router.message(F.text == UserButtons.ADMIN)
async def show_admin_handler(message: Message):
    await message.answer(
        f'👨‍💼 Admin {conf.bot.ADMIN_NUMBER}')


@main_router.message(F.text == UserButtons.CHANGE_FIRST_NAME)
async def send_first_name_handler(message: Message, state: FSMContext) -> None:
    await message.answer("✍️ <b>Ismingizni kiriting</b>", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ChangeFirstNameStates.first_name)


@main_router.message(ChangeFirstNameStates.first_name)
async def change_first_name_handler(message: Message, state: FSMContext) -> None:
    if not message.text.isalpha():
        await wrong_first_last_name(message)
        await send_first_name_handler(message, state)
        return

    await User.update(message.from_user.id, first_name=message.text)
    await message.answer(
        f"Hurmatli <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a> sizning ismingiz {message.text} ga uzgartirildi!")
    await myinfo_command_handler(message)
    await state.clear()


@main_router.message(F.text == UserButtons.CHANGE_LAST_NAME)
async def send_last_name_handler(message: Message, state: FSMContext) -> None:
    await message.answer("✍️ <b>Familiyangizni kiriting</b>", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ChangeLastNameStates.last_name)


@main_router.message(ChangeLastNameStates.last_name)
async def change_last_name_handler(message: Message, state: FSMContext) -> None:
    if not message.text.isalpha():
        await wrong_first_last_name(message)
        await send_last_name_handler(message, state)
        return

    await User.update(message.from_user.id, last_name=message.text)
    await message.answer(
        f"Hurmatli <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a> sizning familiyangiz {message.text} ga uzgartirildi!")
    await myinfo_command_handler(message)
    await state.clear()


@main_router.message(F.text == UserButtons.CHECK_ANSWER)
async def check_send_code_answer_handler(message: Message, state: FSMContext) -> None:
    await message.answer('✍️ Test kodini yuboring.',
                         reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=UserButtons.BACK)]],
                                                          resize_keyboard=True))
    await state.set_state(CheckTestAnswersStates.test_id)


@main_router.message(CheckTestAnswersStates.test_id)
async def check_answer_handler(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit() or (test := await Test.get(int(message.text))) is None:
        await message.answer("❗️ Test kodi noto'g'ri, tekshirib qaytadan yuboring.")
        await check_send_code_answer_handler(message, state)
        return
    if not test.is_active:
        await message.answer(
            "<b>❗ Test yakunlangan, javob yuborishda kechikdingiz keyingi testlarda faol bo'lishingizni kutib qolamiz</b>",
            reply_markup=main_keyboard_btn().as_markup(resize_keyboard=True))
        await state.clear()
        return

    user_answer = await TestAnswer.filter(
        (TestAnswer.user_id == message.from_user.id) & (TestAnswer.test_id == test.id)
    )
    if user_answer:
        user_answer = user_answer[0]
        await message.answer(f"""🔴 Ushbu testda avval qatnashgansiz.
💻 Test kodi: {user_answer.test.id}
✅ Natija: {len(user_answer.accepted_answers)} ta
🎯 Sifat: {(len(user_answer.accepted_answers) / len(user_answer.test.answers) * 100):.1f}%
⏱️ <b>{user_answer.created_at.date()} {user_answer.created_at.hour}:{user_answer.created_at.minute}</b>""",
                             reply_markup=main_keyboard_btn().as_markup(resize_keyboard=True))
        await state.clear()
        return

    await state.update_data(answers=test.answers, test_id=test.id)

    await create_test_answers_send_user_answers(message, state,
                                                f"✍️ {test.id} kodli <b>{test.name}</b> testda {len(test.answers)} ta kalit mavjud. \n<b>Javoblaringizni yuboring</b>.\n")


@main_router.message(CheckTestAnswersStates.user_answers)
async def check_answer_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    try:
        user_answers = {}
        if not message.text.isalnum():
            raise ValueError
        if message.text.isalpha():
            for index, value in enumerate(message.text, 1):
                user_answers[str(index)] = value.lower()
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
                user_answers[str(index)] = value.lower()

    except ValueError:
        await create_test_answers_send_user_answers(message, state,
                                                    "‼Siz kiritgan javoblar formati noto'g'ri, iltimos tekshirib so'ralgan formatda yuboring.")
        return

    test_answers = await state.get_data()
    if len(user_answers) != len(test_answers['answers']):
        await create_test_answers_send_user_answers(message, state,
                                                    "🧐 Siz yuborgan javoblar soni test javoblari soniga mos emas, iltimos tekshirib testda mavjud savollarning barchasiga javob berib yuboring, javoblar kam bo'lishi ham ko'p bo'lishi ham mumkin emas.")
        return

    accepted_answers = {k: v for k, v in test_answers['answers'].items() if user_answers.get(k) == v}
    created_test_answer = await TestAnswer.create(
        test_id=test_answers['test_id'], user_id=message.from_user.id,
        user_answers=user_answers,
        accepted_answers=accepted_answers,
        quality_level=(len(accepted_answers) / len(test_answers['answers']) * 100)
    )
    user = await User.get(message.from_user.id)
    await message.answer(f"""💡 <b>Natijangiz</b>:
🙎🏻‍♂️ <b>Foydalanuvchi</b>: <a href="tg://user?id={message.from_user.id}">{user.last_name} {user.first_name}</a>
💻 <b>Test kodi</b>: {test_answers['test_id']}
✅ <b>To'gri javoblar</b>: {len(accepted_answers)} ta
❌ <b>Noto'g'ri javoblar</b>: {len(test_answers['answers']) - len(accepted_answers)} ta
📊 <b>Sifat</b>: {created_test_answer.quality_level:.1f}%
📆 {created_test_answer.created_at.date()} 🕰 {created_test_answer.created_at.hour}:{created_test_answer.created_at.minute}""",
                         reply_markup=main_keyboard_btn().as_markup(resize_keyboard=True))

    for admin_id in conf.bot.get_admin_list:
        await bot.send_message(admin_id,
                               f"""{test_answers['test_id']} <b>kodli testda </b><b><a href="tg://user?id={message.from_user.id}">{user.last_name} {user.first_name}</a>  qatnashdi!</b> 
✅ <b>Natija(to'gri javob)</b>: {len(accepted_answers)} ta
🎯 <b>Sifat darajasi</b>: {created_test_answer.quality_level:.1f}%
⏱️ <b>{created_test_answer.created_at.date()} {created_test_answer.created_at.hour}:{created_test_answer.created_at.minute}</b>""",
                               reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                   [InlineKeyboardButton(text="📊 Holat", callback_data='test_statistics_' + str(
                                       test_answers['test_id'])),
                                    InlineKeyboardButton(text='⏰ Yakunlash',
                                                         callback_data='stop_test_' + str(test_answers['test_id']))]]))
    await state.clear()
