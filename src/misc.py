from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN=os.getenv('BOT_TOKEN')
PASSWORD = os.getenv('PASSWORD') 
PHOTO1 = "content/photo1.jpg"
PHOTO2 = "content/photo2.jpg"
PHOTO3 = "content/photo3.jpg"
PHOTO4 = "content/photo4.jpg"
PHOTO5 = "content/photo5.jpg"
PHOTO6 = "content/photo6.jpg"

INACTIVE_BAN_THRESHOLD_SECONDS = 4 * 24 * 60 * 60  # 4 дня
BANNED_NOTIFY_THRESHOLD_SECONDS = 15 * 60 * 60  # 15 часов
USER_MANAGEMENT_LOOP_INTERVAL_SECONDS = 60 * 5  # 5 минут

bot_id = BOT_TOKEN.split(":",1)[0]
bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
