from aiogram.fsm.state import StatesGroup, State


class UserStates(StatesGroup):
    first_name = State()
    last_name = State()
    phone_number = State()


class NewsStates(StatesGroup):
    news = State()


class ChangeFirstNameStates(StatesGroup):
    first_name = State()


class ChangeLastNameStates(StatesGroup):
    last_name = State()


class CreateTestStates(StatesGroup):
    name = State()
    answers = State()


class CreateCertificateStates(StatesGroup):
    image = State()


class CheckTestAnswersStates(StatesGroup):
    test_id = State()
    user_answers = State()
    answers = State()
