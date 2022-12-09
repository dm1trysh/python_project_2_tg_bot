import logging
import asyncio
import re
import aioschedule
import pymongo


import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ParseMode
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor


from states import Form, FormSetDate, FormRedDate
from mongobase import insert_new_objects, redact_event, find_event, delete_event,\
    get_all_objects, delete_user
from checking_date_format import check_date_value, check_time_value, check_today_schedule_date,\
    check_whether_date_equals
from config import API_TOKEN


logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


db_client = pymongo.MongoClient("mongodb://localhost:27017")
current_db = db_client["calendar_bot_db"]
collection = current_db["calendar_events"]
collection_current_user = current_db["current_users"]


SCHEDULEEVERYSTEP = 0.05         # frequency of checking DB whether notification is completed or not
SCHEDULEWAIT = 1                 # waiting for executor
TIMETOSHOWSCHEDULE = "10:50"     # time for sending schedule for upcoming day


# start command and start user registration
# essential for every new user in order to get chat id for bot
# user information:
# 1) name
# 2) age
# 3) gender
# 4) chat id for sending messages with notifications back
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await Form.name.set()

    await message.reply("Hey there! What's your name?")


# for finish states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    await state.finish()
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


# input username for registration
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await Form.next()
    await message.reply("How old are you?")


# incorrect user age input
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def process_age_invalid(message: types.Message):
    return await message.reply("Age gotta be a number.\nHow old are you? (digits only)")


# correct user age input
@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(age=int(message.text))

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Male", "Female")
    markup.add("Other")

    await message.reply("What is your gender?", reply_markup=markup)


# incorrect gender input (using markup)
@dp.message_handler(lambda message: message.text not in ["Male", "Female", "Other"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    return await message.reply("Bad gender name. Choose your gender from the keyboard.")


# incorrect gender input (using markup)
# checking user in DB
# if user is new, he will be added in DB
@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gender'] = message.text

        markup = types.ReplyKeyboardRemove()

        user = {
            'name': data['name'],
            'age': data['age'],
            'gender': data['gender'],
            'id': message.from_user.id
        }
        all_collection = get_all_objects(collection_current_user)
        is_in_db = False
        if not(all_collection is None):
            for user_in_db in all_collection:
                if user_in_db['id'] == message.from_user.id:
                    is_in_db = True
        if not is_in_db:
            insert_new_objects(collection_current_user, user)

        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Hi! Nice to meet you,', md.bold(data['name'])),
                md.text('Age:', md.code(data['age'])),
                md.text('Gender:', data['gender']),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    button_set = KeyboardButton(text="set new event")
    button_redact = KeyboardButton(text="redact your event")
    button_help = KeyboardButton(text="help")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(button_set).add(button_redact).add(button_help)
    await state.finish()
    await message.answer("Now choose commands", reply_markup=keyboard)


# add new event in collection command
# input:
# 1) new event name
# 2) date for notification
# 3) time for notification
@dp.message_handler(Text(equals="set new event"))
@dp.message_handler(commands='setevent')
async def cmd_set_event(message: types.Message):
    await FormSetDate.user_event.set()

    await message.reply("Eneter your event, please")


# event's name input
@dp.message_handler(state=FormSetDate.user_event)
async def process_user_event(message: types.Message, state: FSMContext):
    async with state.proxy() as data_event:
        data_event['user_event'] = message.text

    await FormSetDate.next()
    await message.reply("Now choose the date, please (dd.mm.yyyy)")


# incorrect date input
@dp.message_handler(lambda message: (re.fullmatch(r'\d\d\.\d\d\.\d{4}', message.text) is None),\
                    state=FormSetDate.user_date)
async def process_date_invalid(message: types.Message):
    return await message.reply("Enter correct date, please")


# correct date input
@dp.message_handler(lambda message: not(re.fullmatch(r'\d\d\.\d\d\.\d{4}', message.text) is None),\
                    state=FormSetDate.user_date)
async def process_set_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_event:
        data_event['user_date'] = message.text

    await FormSetDate.next()
    await message.reply("Now please choose the time (hh:mm)")


# incorrect time input
@dp.message_handler(lambda message: (re.fullmatch(r'\d\d:\d\d', message.text) is None),\
                    state=FormSetDate.user_time)
async def process_set_time(message: types.Message):
    return await message.reply("Enter correct time, please")


# correct time input and adding new event in collection
@dp.message_handler(lambda message: not(re.fullmatch(r'\d\d:\d\d', message.text) is None),\
                    state=FormSetDate.user_time)
async def process_set_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data_event:
        data_event['user_time'] = message.text

        result_date_checking = check_date_value(data_event['user_date'].split('.'))
        result_time_checking = check_time_value(data_event['user_time'].split(':'))

        if not(result_date_checking and result_time_checking):
            await bot.send_message(message.from_user.id, "You added incorrect date or time")
            await state.finish()
            return

        await bot.send_message(
            message.chat.id,
            md.text(
                "Your event has been added",
                md.text(data_event['user_event']),
                md.text(data_event['user_date']),
                md.text(data_event['user_time']),
                sep='\n',
            )
        )

        all_users_in_collection = get_all_objects(collection_current_user)
        user_name = ''
        for one_user in all_users_in_collection:
            if one_user['id'] == message.from_user.id:
                user_name = one_user['name']
                break
        new_event = {
            'event': md.text(data_event['user_event']),
            'date': md.text(data_event['user_date']),
            'time': md.text(data_event['user_time']),
            'user_id': md.text(message.from_user.id),
            'user_name': user_name
        }
        insert_new_objects(collection, new_event)

    await state.finish()


# redact event command
# input:
# 1) name to search through events in DB
# 2) date to arrange event
# 3) time to arrange event
@dp.message_handler(Text(equals="redact your event"))
@dp.message_handler(commands='redactevent')
async def cmd_redact_event(message: types.Message):
    await FormRedDate.user_event.set()

    await message.reply("Eneter event, you would like to change, please")


# event's name input
@dp.message_handler(state=FormRedDate.user_event)
async def process_user_event(message: types.Message, state: FSMContext):
    async with state.proxy() as data_event:
        data_event['user_event'] = message.text

    await FormRedDate.next()
    await message.reply("Now choose new date, please (dd.mm.yyyy)")


# incorrect date input
@dp.message_handler(lambda message: (re.fullmatch(r'\d\d\.\d\d\.\d{4}', message.text) is None),\
                    state=FormRedDate.user_date)
async def process_date_invalid(message: types.Message):
    return await message.reply("Enter correct date, please")


# correct date input
@dp.message_handler(lambda message: not(re.fullmatch(r'\d\d\.\d\d\.\d{4}', message.text) is None),\
                    state=FormRedDate.user_date)
async def process_redact_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_event:
        data_event['user_date'] = message.text

    await FormRedDate.next()
    await message.reply("Now choose new time, please (hh:mm)")


# incorrect time input
@dp.message_handler(lambda message: (re.fullmatch(r'\d\d:\d\d', message.text) is None),\
                    state=FormRedDate.user_time)
async def process_set_time(message: types.Message):
    return await message.reply("Enter correct time, please")


# correct time input and changing event in collection
@dp.message_handler(lambda message: not(re.fullmatch(r'\d\d:\d\d', message.text) is None),\
                    state=FormRedDate.user_time)
async def process_redact_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data_event:
        data_event['user_time'] = message.text

        result_date_checking = check_date_value(data_event['user_date'].split('.'))
        result_time_checking = check_time_value(data_event['user_time'].split(':'))

        if not(result_date_checking and result_time_checking):
            await bot.send_message(message.from_user.id, "You added incorrect date or time")
            await state.finish()
            return

        updated_event = {
            'date': md.text(data_event['user_date']),
            'time': md.text(data_event['user_time'])
        }

        result = redact_event(collection, md.text(data_event['user_event']), updated_event)
        if result == False:
            await bot.send_message(message.chat.id, "This event doesn't exist")
            await state.finish()
        else:
            await bot.send_message(
                message.chat.id,
                md.text(
                    "Event date and time have been redacted",
                    md.text(data_event['user_event']),
                    md.text(data_event['user_date']),
                    md.text(data_event['user_time']),
                    sep='\n',
                )
            )

    await state.finish()


# help command
@dp.message_handler(Text(equals="help"))
@dp.message_handler(commands='help')
async def cmd_help(message: types.Message):
    await message.reply(md.text(
            "Here're possible bot commands:",
            "1) setevent to add new event",
            "then type date (dd.mm.yyyy)",
            "then type time (hh:mm)",
            "2) redactevent to redact event",
            "then type date (dd.mm.yyyy)",
            "then type time (hh:mm)",
            "",
            "And then bot will send you notification",
            sep='\n'
        )
    )


# sending notification if current event happens
async def check_events_in_db():
    all_collection = get_all_objects(collection)
    if all_collection is None:
        return

    for event in all_collection:
        event_date = event['date'].split('.')
        event_time = event['time'].split(':')

        is_the_same = check_whether_date_equals(event_date, event_time)
        is_past = not(check_date_value(event_date) and check_time_value(event_time))

        if is_past:
            delete_event(collection, event['event'])
            continue

        if is_the_same:
            await bot.send_message(str(event['user_id']),
                md.text(
                    'Dear,',
                    event['user_name'],
                    '!',
                    sep=' '
                )
            )
            await bot.send_message(str(event['user_id']),
                md.text(
                    'You have an event:',
                    event['event'],
                    'at this time',
                    sep='\n'
                )
            )
            delete_event(collection, event['event'])


# sending for every user their schedule for every day
async def check_schedule():
    all_collection = get_all_objects(collection)
    if all_collection is None:
        return

    for event in all_collection:
        is_today = check_today_schedule_date(event['date'].split('.'))
        if is_today:
            await bot.send_message(event['user_id'],
                md.text(
                    "You have",
                    event['event'],
                    'at',
                    event['time'],
                    'today',
                    sep=' '
                )
            )


# activating check_schedule every day to show schedule for today
# activating check_events_in_db to send notification
async def scheduler():
    aioschedule.every(SCHEDULEEVERYSTEP).minutes.do(check_events_in_db)
    aioschedule.every().day.at(TIMETOSHOWSCHEDULE).do(check_schedule)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(SCHEDULEWAIT)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)