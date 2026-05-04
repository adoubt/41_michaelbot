import urllib.parse
import re
import asyncio
from aiogram.filters import Filter
from aiogram.types import Message, ContentType, InputMediaPhoto, InputMediaVideo, FSInputFile
from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramForbiddenError
from src.methods.database.users_manager import UsersDatabase
from src.methods.database.config_manager import ConfigDatabase
from src.methods.database.ads_manager import AdsDatabase
from loguru import logger
from typing import Union, List
from time import time
from datetime import datetime
from src.locales.es import LOCALES
from src.keyboards import user_keyboards
from src.misc import bot, PHOTO1, PHOTO2, PHOTO3, PHOTO4, PHOTO5, PHOTO6
PHOTO_PATHS = {
    "photo1": PHOTO1,
    "photo2": PHOTO2,
    "photo3": PHOTO3,
    "photo4": PHOTO4,
    "photo5": PHOTO5,
    "photo6": PHOTO6,
}

async def get_or_set_photo_id(key: str, file_path: str, message: Message):
    photo_id = await ConfigDatabase.get_value(key)

    if photo_id:
        return photo_id

    msg = await message.answer_photo(photo=file_path)
    photo_id = msg.photo[-1].file_id

    await ConfigDatabase.set_value(key, photo_id)
    return photo_id

def get_file_id(message: Message, file_type: str) -> str:
    """Проверка основного сообщения"""
    if message.audio and file_type in ['mp3', 'preview']:
        return message.audio.file_id
    elif message.document and file_type in ['wav', 'stems']:
        return message.document.file_id
    #Проверка вложенного сообщения
    elif message.reply_to_message:
        if message.reply_to_message.audio and file_type in ['mp3', 'preview']:
            return message.reply_to_message.audio.file_id
        elif message.reply_to_message.document and file_type in ['wav', 'stems']:
            return message.reply_to_message.document.file_id
    return None

def parse_callback_data(data: str) -> dict:
    """Удаляем префикс и парсим параметры"""
    query_string = data.split(':', 1)[1]
    return dict(urllib.parse.parse_qsl(query_string))

async def parse_int_arg(message: Message, args: list[str], index: int = 1, usage: str | None = None):
    if len(args) <= index:
        if usage:
            await message.answer(usage)
        return None
    try:
        return int(args[index])
    except (ValueError, TypeError):
        await message.answer("ID должен быть числом.")
        return None


async def send_currency_pairs_message(user_id: int):
    """Отправляет сообщение с выбором валютных пар после активации."""
    
    photo1 = await ConfigDatabase.get_value("photo1") 
    await bot.send_photo(user_id, photo=photo1, caption =LOCALES["currency_pairs"],parse_mode="HTML", reply_markup=user_keyboards.currency_pairs_kb())


def is_valid_email(email):
    """Определение шаблона для валидации email-адреса"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email)






# async def is_user_subscribed(user_id: int, **kwargs):

#     member = await bot.get_chat_member(int(CHANNEL_ID), user_id)
#     if member.status in ["member", "creator", "administrator"]:
#         return True
#     else:
#         return False
    

async def get_bot_username(bot: Bot):
    me = await bot.get_me()
    return me.username 



class AdStateFilter(Filter):
    def __init__(self, required_state: str):
        self.required_state = required_state

    async def __call__(self, message: Message) -> bool:
        state = await ConfigDatabase.get_value("ad_state")
        return state == self.required_state 
    

async def send_ad_message(user_id, content: Union[Message, List[Message]]):
    
    try:
        # --- медиагруппа ---
        if isinstance(content, list):
            
            caption = None

            for msg in content:
                if msg.html_text:
                    caption = msg.html_text
                    break
            media = []
            for i, msg in enumerate(content):
                cap = caption if i == 0 else None

                if msg.photo:
                    media.append(InputMediaPhoto(
                        media=msg.photo[-1].file_id,
                        caption=cap,
                        parse_mode="HTML"
                    ))

                elif msg.video:
                    media.append(InputMediaVideo(
                        media=msg.video.file_id,
                        caption=cap,
                        parse_mode="HTML"
                    ))

            if media:
                msgs = await bot.send_media_group(user_id, media,)
                return [m.message_id for m in msgs]

            return False

        # --- одиночное сообщение ---
        message = content

        if message.content_type == ContentType.TEXT:
            msg = await bot.send_message(
                user_id,
                message.html_text,
                parse_mode="HTML"
            )
            return msg.message_id
        
        elif message.content_type == ContentType.PHOTO:
            msg = await bot.send_photo(
                user_id,
                message.photo[-1].file_id,
                caption=message.html_text,
                parse_mode="HTML"
            )
            return msg.message_id
        
        elif message.content_type == ContentType.VIDEO:
            msg = await bot.send_video(
                user_id,
                message.video.file_id,
                caption=message.html_text,
                parse_mode="HTML"
            )
            return msg.message_id
        
        elif message.content_type == ContentType.ANIMATION:
            msg = await bot.send_animation(
                user_id,
                message.animation.file_id,
                caption=message.html_text,
                parse_mode="HTML"
            )
            return msg.message_id
        

    except Exception as e:
        logger.error(f"Ошибка при отправке {user_id}: {e}")
        return False

async def handle_send_ad(content, admin: int):
    state = await ConfigDatabase.get_value("ad_state")

    message = content if isinstance(content, Message) else content[0]

    if state == "off":
        await message.answer("Рассылка сейчас выключена! Переключить режим рассылки можно здесь /mode")
        return

    ad_id = int(time())

    users = {
        "all": await UsersDatabase.get_all(),
        "test": [[admin]],
        "admins": await UsersDatabase.get_all_admins(),
        "blocked": await UsersDatabase.get_blocked_users(),
        "not_activated": await UsersDatabase.get_not_activated_users(),
        "activated": await UsersDatabase.get_activated_users()
    }.get(state, [])

    sent_count = 0
    blocked_times = 0   
    for user in users:
        if await UsersDatabase.is_banned(user[0]):
            continue
        try:
            msg_ids = await send_ad_message(user[0], content)

            if not msg_ids:
                blocked_times += 1
                continue

            sent_count += 1

            if isinstance(msg_ids, list):
                await AdsDatabase.add_many(ad_id, user[0], msg_ids)
            else:
                await AdsDatabase.add(ad_id, user[0], msg_ids)

            

        except Exception as e:
            # все остальные ошибки
            logger.error(f"Error while sending to {user[0]}: {e}")

        await asyncio.sleep(0.04)

    admin_name = await UsersDatabase.get_value(admin, 'username')

    msg = (
        f"📢 Messages sent: <b>{sent_count}</b>\n"
        f"Errors: <code>{blocked_times}</code>\n"
        f"Sender: @{admin_name} {admin}\n"
        f"state: <b>{state}</b>\n"
        f"ad_id: <code>{ad_id}</code>"
        "Чтобы удалить рассылку используй /redakt_post"
    )
    admins = await UsersDatabase.get_all_admins()
    for a in admins:
        try:
            await bot.send_message(a[0], msg, parse_mode="HTML")
        except Exception:
            pass

    logger.success(msg)

async def init_content_handler(message: Message):
    for key, path in PHOTO_PATHS.items():
        msg = await message.answer_photo(photo=FSInputFile(path))
        
        file_id = msg.photo[-1].file_id
        await ConfigDatabase.set_value(key, file_id)

    await message.answer("content initialized")


async def ban_user(user_id: int):
    """Банит пользователя, отправляет уведомление и обновляет last_block_notify_at."""
    await UsersDatabase.ban(user_id)
    await UsersDatabase.set_value(user_id, 'last_block_notify_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        await bot.send_message(user_id, LOCALES["blocked"], parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Failed to notify user {user_id}: {e}")
    logger.info(f"User {user_id} banned")