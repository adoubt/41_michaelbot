from src.methods.database.users_manager import UsersDatabase
from aiogram.types import Message, CallbackQuery
from functools import wraps
from src.locales.es import LOCALES
from loguru import logger
from src.misc import bot, bot_id
# from src.methods.utils import  is_user_subscribed
from src.keyboards import user_keyboards
# def new_seller_handler(function):
#     async def _new_seller_handler(*args, **kwargs):
#         message: Message = args[0]
#         user_id = message.from_user.id
#         if (await UsersDatabase.get_value(user_id, 'is_seller')) == 0:
#             await UsersDatabase.set_value(user_id, 'is_seller', 1)
#             await LicensesDatabase.set_default(user_id)
#         return await function(*args, **kwargs)

#     return _new_seller_handler


def new_user_handler(function):
    async def _new_user_handler(*args, **kwargs):
        message: Message = args[0]
        user_id = message.from_user.id
        
        if (await UsersDatabase.get_user(user_id)) == -1:
            username = message.from_user.username
            language = message.from_user.language_code
            
            
            await UsersDatabase.create_user(
                user_id=user_id,
                username=username,
                language=language,
                
            )

            msg = f"👤 @{username} {user_id}"

            # защита от None + любых ошибок отправки
            

            logger.success(f"Новый пользователь (ID: {user_id} username {username})")

            if user_id == int(bot_id):
                await UsersDatabase.set_value(user_id, 'is_admin', 1)
                logger.info(f'[Admin] {user_id} получил права админа')

        return await function(*args, **kwargs)

    return _new_user_handler


# def pursue_subscription(function):
#     async def _pursue_subscription(*args, **kwargs):
#         msg = args[0]
#         if msg is None:
#             return

#         if (await is_user_subscribed(msg.from_user.id)) or (
#                 type(msg) is CallbackQuery and (await is_user_subscribed(msg.message.from_user.id))):
#             return await function(*args, **kwargs)
#         msg_text = f'Для использования бота необходимо подписаться на канал.\n<a href="{CHANNEL_LINK}">Подписаться (кликабельно)</a>'
       
        

#         await msg.answer(text=msg_text, parse_mode ="HTML",reply_markup=user_keyboards.get_subscription_kb(CHANNEL_LINK))
#         return

#     return _pursue_subscription

def is_admin(function):
    async def _is_admin(*args, **kwargs):
        message: Message = args[0]
        user_id = message.from_user.id
        if await UsersDatabase.is_admin(user_id) or user_id == int(bot_id):
            return await function(*args, **kwargs)
        await message.answer('You don\'t have admin rights')
        return

    return _is_admin



def is_not_banned(function):
    @wraps(function)
    async def wrapper(event: Message, **kwargs):

        user_id = event.from_user.id

        if await UsersDatabase.is_banned(user_id):
            await event.answer(LOCALES["blocked"], parse_mode="HTML")
            return

        return await function(event, **kwargs)

    return wrapper


def is_activated(function):
    @wraps(function)
    async def wrapper(event, **kwargs):
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            user_id = event.from_user.id

        if await UsersDatabase.get_value(user_id, 'is_activated') != 1:
            if isinstance(event, CallbackQuery):
                await event.message.answer(LOCALES["activate_access"], parse_mode="HTML")
            else:
                await event.answer(LOCALES["activate_access"], parse_mode="HTML")
            return

        return await function(event, **kwargs)

    return wrapper


def track_activity(function):
    @wraps(function)
    async def wrapper(*args, **kwargs):
        event = args[0]
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:  # Message
            user_id = event.from_user.id
        await UsersDatabase.update_last_activity(user_id)
        return await function(*args, **kwargs)

    return wrapper
