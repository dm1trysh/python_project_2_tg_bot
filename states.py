from imports import *

class Form(StatesGroup):
    name = State()
    age = State()
    gender = State()


class FormSetDate(StatesGroup):
    user_event = State()
    user_date = State()
    user_time = State()


class FormRedDate(StatesGroup):
    user_event = State()
    user_date = State()
    user_time = State()
