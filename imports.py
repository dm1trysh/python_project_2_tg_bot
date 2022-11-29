import logging
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
import re
import datetime

from datetime import datetime
import asyncio
import aioschedule

from threading import Thread
from time import sleep

import pymongo