from aiogram.dispatcher.filters.state import State, StatesGroup


class Form(StatesGroup):   # for user registration
    name = State()
    age = State()
    gender = State()


class FormSetDate(StatesGroup):  # for setting event
    user_event = State()
    user_date = State()
    user_time = State()


class FormRedDate(StatesGroup):  # for redacting event
    user_event = State()
    user_date = State()
    user_time = State()
