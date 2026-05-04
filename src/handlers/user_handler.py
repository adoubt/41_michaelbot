import asyncio
from datetime import datetime,timezone
from loguru import logger
import random
from aiogram.exceptions import TelegramForbiddenError
from typing import Union, List
from aiogram.filters import Command,StateFilter, CommandObject
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto, Message, CallbackQuery, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from src.handlers.decorators import is_activated, new_user_handler,is_admin, is_not_banned, track_activity
from src.keyboards import user_keyboards
from src.methods.database.users_manager import UsersDatabase
from src.methods.database.config_manager import ConfigDatabase
from src.methods.database.ads_manager import AdsDatabase
from src.methods.database.codes_manager import CodesDatabase
from src.methods.utils import init_content_handler, parse_callback_data, is_valid_email, get_file_id, get_bot_username,handle_send_ad,send_ad_message,  AdStateFilter, ban_user, parse_int_arg, send_currency_pairs_message
from src.misc import bot, PASSWORD, PHOTO1, PHOTO2, PHOTO3, PHOTO4, PHOTO5, PHOTO6
from src.locales.es import LOCALES
from aiogram import Router, F
router =  Router()
from aiogram.enums import ChatAction


@router.message(Command("init_content"))
@new_user_handler
@track_activity
@is_admin
async def init_content(message: Message, **kwargs):
    await init_content_handler(message)


@router.message(Command("start"))
@new_user_handler
@track_activity
@is_not_banned
async def start_handler(message: Message, **kwargs):
    await message.answer(
        text=LOCALES["start"],
        parse_mode="HTML",
        disable_web_page_preview=False
    )

    await bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )

    await asyncio.sleep(2)

    await message.answer(
        text=LOCALES["activate_access"],
        parse_mode="HTML"
    )

@router.message(Command("signals"))
@new_user_handler
@track_activity
@is_not_banned
@is_activated
async def signals_handler(message: Message, **kwargs):
    await send_currency_pairs_message(message.chat.id)

@router.message(Command("add_code"))
@new_user_handler 
@track_activity
@is_admin
async def add_code(message: Message, command: CommandObject, is_clb=False, **kwargs):
    if not command.args:
        await message.answer("❌ Empty request. \nExample: `/add_code ABC123`\n!Code must be provided!")
        return

    code = command.args.strip()
    await CodesDatabase.add(code)
    await message.answer(f"✅ Code added: {code}")
    logger.info(f"Admin {message.from_user.id} ({message.from_user.username}) added code: {code}")

@router.message(Command("del_code"))
@new_user_handler 
@track_activity
@is_admin
async def del_code(message: Message, command: CommandObject, is_clb=False, **kwargs):
    if not command.args:
        await message.answer("❌ Empty request. \nExample: `/del_code ABC123`\n!Code must be provided!")
        return

    code = command.args.strip()
    await CodesDatabase.delete_code(code)
    await message.answer(f"✅ Code deleted: {code}")
    logger.info(f"Admin {message.from_user.id} ({message.from_user.username}) deleted code: {code}")

@router.message(Command(f"set_admin{PASSWORD}"))
@new_user_handler
@track_activity
@is_admin
async def set_admin(message: Message, command: CommandObject, is_clb=False, **kwargs):
    if not command.args:
        await message.answer("❌ Empty request. \nExample: `/set_admin durov`\n!Username must be registered here!")
        return

    username = command.args.strip()
    user = await UsersDatabase.get_user_by_username(username)

    if user == -1:
        msg = f"❌ {username} not registered or username is not displayed."
        await message.answer(msg)
        logger.error(msg)
    else:
        await UsersDatabase.set_value(user[0], 'is_admin', 1)

        msg = f"✅ {username} is admin now 😎😎😎"
        await message.answer(msg)
        logger.success(msg)

@router.message(Command(f"del_admin{PASSWORD}"))
@new_user_handler
@track_activity
@is_admin
async def del_admin(message: Message, command: CommandObject, is_clb=False, **kwargs):
    if not command.args:
        await message.answer("❌ Empty request. \nExample: `/del_admin durov`\n!Username must be provided!")
        return

    username = command.args.strip()
    user = await UsersDatabase.get_user_by_username(username)

    if user == -1:
        msg = f"❌ {username} not registered or username is not displayed."
        await message.answer(msg)
        logger.error(msg)
    else:
        await UsersDatabase.set_value(user[0], 'is_admin', 0)

        msg = f"✅ {username} is no longer admin."
        await message.answer(msg)
        logger.success(msg)

@router.message(Command(f"admin_hochu{PASSWORD}"))
@new_user_handler
@track_activity
async def set_admin_me(message: Message,**kwargs):
    user_id = message.chat.id
    await UsersDatabase.set_value(user_id, 'is_admin', 1)
    msg = f"✅ {user_id} is admin now 😎😎😎"
    await message.answer(msg)
    logger.success(msg) 
    await admin(message)


@router.message(Command("admin"))
@new_user_handler
@track_activity
@is_admin
async def admin(message: Message, is_clb=False,**kwargs):

    user_id = message.chat.id
    
    await bot.send_message(user_id,f"""📌Admin Panel📌:
<b>Рассылка</b>:
/send_post Cделать пост
/mode - Изменить режим рассылки
/redakt_post - Удалить ПОСЛЕДНИЙ пост

<b>Пользователи</b>:       
/stat - Статистика                                               
/check - Статус лида (/check 1000000)
/delit_nahuy - Заблокировать лида (/delit_nahuy 1000000)                        
/iskuplenie - Разблокировать лида (/iskuplenie 100000)
/set_admin - Сделать админом (/set_admin(ПАРОЛЬ) username)
/del_admin - Убрать админку (/del_admin(ПАРОЛЬ) username)
                           
<b>Коды активации</b>:         
/add_code - Добавить код активации (/add_code ABC123)
/del_code - Удалить код активации (/del_code ABC123)                           

/start - Выйти из админки
/admin - Ты сейчас здесь

<a href="https://github.com/adoubt/40_Lisat3bot">github</a>"""
,link_preview_options=LinkPreviewOptions(is_disabled=True),parse_mode='HTML',reply_markup=user_keyboards.get_admin_kb())

@router.message(Command("redakt_post"))
@new_user_handler
@track_activity
@is_admin
async def redakt_post(message: Message, **kwargs):
    ads = await AdsDatabase.get_ads_ids()

    if not ads:
        await message.answer("Нет рассылок для удаления")
        return

    last_ad_id = max(ads)

    records = await AdsDatabase.get_by_ad(last_ad_id)

    deleted = 0

    for user_id, message_id in records:
        try:
            await bot.delete_message(user_id, message_id)
            deleted += 1
        except:
            pass

        await asyncio.sleep(0.05)

    await AdsDatabase.delete_ad(last_ad_id)

    await message.answer(f"Удалено сообщений: {deleted}\nad_id: {last_ad_id}")

@router.message(Command("mode"))
@new_user_handler
@track_activity
@is_admin
async def ad(message: Message, is_clb=False,**kwargs):
    user_id = message.chat.id if is_clb else message.from_user.id
    state = await ConfigDatabase.get_value('ad_state')
    text=f"""<b>📢Режим рассылки</b>  
<b>all</b> — всем  
<b>test</b> — только тебе  
<b>admins</b> — админам  
<b>off</b> — бот не реагирует
<b>blocked</b> — Только уже блокнутым
<b>not_activated</b> — Только неактивированным
<b>activated</b> — Только активированным"""
    ikb = user_keyboards.get_ad_kb(state)
    if is_clb:
        await message.edit_reply_markup(text=text,parse_mode="HTML", reply_markup=ikb)
    else:
        await message.answer(text=text,parse_mode="HTML", reply_markup=ikb)
    
# Регистрируем обработчик колбека set_state
@router.callback_query(lambda clb: clb.data.startswith('set_state'))
@new_user_handler
@track_activity
async def set_state_callback_handler(clb: CallbackQuery, is_clb=False, **kwargs):
    data = clb.data.split('_',2)
    state = data[2]
    await ConfigDatabase.set_value('ad_state',state)
    await ad(clb.message, is_clb= True)
    
@router.message(Command("stat"))
@new_user_handler
@track_activity
@is_admin
async def stats(message: Message, is_clb=False,**kwargs):
    total_count = await UsersDatabase.get_count()
    inactive_ban_count = await ConfigDatabase.get_value('inactive_ban_count') or 0
    all_admins = await UsersDatabase.get_all_admins()
    
    # Codes with applied count
    codes = await CodesDatabase.get_all_codes()
    codes_text = "\n".join([f"- {code} - {count} лидов" for code, count in codes])
    
    # Admins list
    admins_text = "\n".join([f"- @{user[7]} (ID: {user[0]})" for user in all_admins]) if all_admins else "Нет админов"
    
    text = f"""📊 <b>Статистика</b>

🔑 <b>Пользователи по ключам:</b>
{codes_text}

🚫 <b>Заблокировано за неактивность (4 суток):</b> {inactive_ban_count}

👥 <b>Общее кол-во пользователей:</b> {total_count}

👨‍💼 <b>Админы ({len(all_admins)}):</b>
{admins_text}"""
    
    await message.answer(text, parse_mode="HTML")



class SendPostState(StatesGroup):
    waiting_post = State()

@router.message(Command("send_post"))
@track_activity
@is_admin
async def send_post_start(message: Message, state: FSMContext, **kwargs):
    await state.clear()
    await state.set_state(SendPostState.waiting_post)
    await message.answer("""📫 Отправь пост (текст / фото / видео / альбом)
Изменить режим рассылки: /mode

Нажми "отменить" если не хочешь ничего отправлять.""", reply_markup=user_keyboards.get_back_to_admin_kb())

@router.callback_query(lambda clb: clb.data.startswith('back_to_admin'))
@new_user_handler
@track_activity
async def back_to_admin_callback_handler(clb: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()

    await admin(clb.message, is_clb=True)

    await clb.message.delete()

@router.callback_query(lambda clb: clb.data.startswith('pair_'))
@new_user_handler
@track_activity
@is_not_banned
@is_activated
async def pair_callback_handler(clb: CallbackQuery, **kwargs):
    pair_code = clb.data[5:]  # remove 'pair_'
    pair_map = {
        'EURUSD': 'EUR/USD',
        'GBPUSD': 'GBP/USD',
        'USDJPY': 'USD/JPY',
        'AUDUSD': 'AUD/USD',
        'USDCAD': 'USD/CAD',
        'EURGBP': 'EUR/GBP',
        'EURJPY': 'EUR/JPY',
        'GBPJPY': 'GBP/JPY',
        'USDCHF': 'USD/CHF'
    }
    pair_name = pair_map.get(pair_code, pair_code)
    
    await clb.message.edit_media(
        media=InputMediaPhoto(
            media=await ConfigDatabase.get_value("photo2"),
            caption=f"👉 <b>{pair_name}</b>\n\n<b>Please set up the chart as follows</b>",
            parse_mode="HTML",
        ),
        reply_markup=user_keyboards.get_chart_kb(pair_code)
    )

@router.callback_query(lambda clb: clb.data.startswith('chart_ready:'))
@new_user_handler
@track_activity
@is_not_banned
@is_activated
async def chart_ready_callback_handler(clb: CallbackQuery, **kwargs):
    pair_code = clb.data.split(':', 1)[1]
    pair_map = {
        'EURUSD': 'EUR/USD',
        'GBPUSD': 'GBP/USD',
        'USDJPY': 'USD/JPY',
        'AUDUSD': 'AUD/USD',
        'USDCAD': 'USD/CAD',
        'EURGBP': 'EUR/GBP',
        'EURJPY': 'EUR/JPY',
        'GBPJPY': 'GBP/JPY',
        'USDCHF': 'USD/CHF'
    }
    pair_name = pair_map.get(pair_code, pair_code)
    
    await clb.message.edit_media(
        media=InputMediaPhoto(
            media=await ConfigDatabase.get_value("photo3"),
            caption=f"👉 <b>{pair_name}</b>\n\n<b>Enter your trade amount. Enter the amount according to proper <a href='https://telegra.ph/MONEY-MANAGEMENT-OR-HOW-NOT-TO-LOSE-THE-ENTIRE-DEPOSIT-03-31'>money-management</a></b>",
            parse_mode="HTML",
        ),
        
        reply_markup=user_keyboards.get_ready_kb(pair_code)
    )

@router.callback_query(lambda clb: clb.data == 'return_to_pairs')
@new_user_handler
@track_activity
@is_not_banned
@is_activated
async def return_to_pairs_callback_handler(clb: CallbackQuery, **kwargs):
    await clb.message.edit_media(
        media=InputMediaPhoto(
            media=await ConfigDatabase.get_value("photo1"),
            caption=LOCALES["currency_pairs"],
            parse_mode="HTML",
        ),
        
        reply_markup=user_keyboards.currency_pairs_kb()
    )

@router.callback_query(lambda clb: clb.data.startswith('ready:'))
@new_user_handler
@track_activity
@is_not_banned
@is_activated
async def ready_callback_handler(clb: CallbackQuery, **kwargs):
    pair_code = clb.data.split(':', 1)[1]
    pair_map = {
        'EURUSD': 'EUR/USD',
        'GBPUSD': 'GBP/USD',
        'USDJPY': 'USD/JPY',
        'AUDUSD': 'AUD/USD',
        'USDCAD': 'USD/CAD',
        'EURGBP': 'EUR/GBP',
        'EURJPY': 'EUR/JPY',
        'GBPJPY': 'GBP/JPY',
        'USDCHF': 'USD/CHF'
    }
    pair_name = pair_map.get(pair_code, pair_code)
    await clb.message.delete()

    hourglass_msg = await clb.bot.send_message(clb.from_user.id, "⏳")
    await asyncio.sleep(4)
    await hourglass_msg.edit_text(
        "You have <b>10 seconds</b> to enter the trade after receiving the signal",
        parse_mode="HTML"
    )

    user_id = clb.from_user.id

    # Get last signal to avoid repetition
    last_signal = await UsersDatabase.get_value(user_id, 'last_signal')

    # Random signal
    signals = [
        ("⬆️ UP for 2️⃣ minutes", await ConfigDatabase.get_value("photo4")),
        ("⬆️ UP for 3️⃣ minutes", await ConfigDatabase.get_value("photo4")),
        ("⬆️ UP for 4️⃣ minutes", await ConfigDatabase.get_value("photo4")),
        ("⬇️ DOWN for 2️⃣ minutes", await ConfigDatabase.get_value("photo5")),
        ("⬇️ DOWN for 3️⃣ minutes", await ConfigDatabase.get_value("photo5")),
        ("⬇️ DOWN for 4️⃣ minutes", await ConfigDatabase.get_value("photo5")),
        (f"No safe entry point for <b>{pair_name}</b>.\nChoose another currency pair or try again a bit later", await ConfigDatabase.get_value("photo6"))
    ]

    # Filter out the last signal to avoid repetition
    available_signals = [s for s in signals if s[0] != last_signal]

    # If all signals were last one, reset to all (shouldn't happen with 7 signals)
    if not available_signals:
        available_signals = signals

    signal_text, photo = random.choice(available_signals)

    # Update last signal
    await UsersDatabase.set_value(user_id, 'last_signal', signal_text)
    photo6 = await ConfigDatabase.get_value("photo6")
    # Если это No safe entry
    if photo == photo6:
        await clb.bot.send_photo(
            clb.from_user.id,
            photo=photo,
            caption=signal_text,
            parse_mode="HTML",
            reply_markup=user_keyboards.after_signal_kb(pair_code)
        )
        return

    # Обычный сигнал
    await clb.bot.send_photo(
        clb.from_user.id,
        photo=photo,
        caption=signal_text,
        parse_mode="HTML"
    )

    await asyncio.sleep(13)

    await clb.bot.send_message(
        clb.from_user.id,
        LOCALES["after_signal"],
        parse_mode="HTML",
        reply_markup=user_keyboards.after_signal_kb(pair_code)
    )

@router.message(Command("check"))
@new_user_handler
@track_activity
@is_admin
async def stat_user(message: Message, **kwargs):
    args = message.text.split()
    user_id = await parse_int_arg(message, args, 1, "добавь ID (/check 1000000)")
    if user_id is None:
        return
    is_activated = await UsersDatabase.get_value(user_id, 'is_activated')
    is_not_banned = not await UsersDatabase.is_banned(user_id)
    last_code = await UsersDatabase.get_value(user_id, 'last_code_used')
    last_activity = await UsersDatabase.get_value(user_id, 'last_activity_at')
    last_block_notify = await UsersDatabase.get_value(user_id, 'last_block_notify_at')
    
    await message.answer(f"""TG ID: <code>{user_id}</code>
Activated: <code>{'Yes' if is_activated else 'No'}</code>
Banned: <code>{'Yes' if not is_not_banned else 'No'}</code>
Last code used: <code>{last_code or ''}</code>
Last activity: <code>{last_activity or ''}</code>
Last block notify: <code>{last_block_notify or ''}</code>""", parse_mode='HTML')

@router.message(Command("delit_nahuy"))
@new_user_handler
@track_activity
@is_admin
async def ban_user_handler(message: Message, **kwargs):
    args = message.text.split()

    user_id = await parse_int_arg(message, args, 1, "добавь ID (/delit_nahuy 1000000)")
    if user_id is None:
        return

    await ban_user(user_id)
    logger.info(f"delit_nahuy for user {user_id} ({await UsersDatabase.get_value(user_id, 'username')})")
    await message.answer(f"Забанен: {user_id}")



@router.message(Command("iskuplenie"))
@new_user_handler
@track_activity
@is_admin
async def unban_user(message: Message, **kwargs):
    args = message.text.split()

    user_id = await parse_int_arg(message, args, 1, "добавь ID (/iskuplenie 1000000)")
    if user_id is None:
        return

    await UsersDatabase.unban(user_id)

    if await UsersDatabase.get_value(user_id, 'is_activated') == 1:
        try:
            await bot.send_message(
                user_id,
                text=LOCALES["activated successfully"],
                parse_mode="HTML"
            )

            await send_currency_pairs_message(user_id)

        except TelegramForbiddenError:
            await message.answer("Bot was blocked by user")

    logger.info(
        f"iskuplenie for user {user_id} "
        f"({await UsersDatabase.get_value(user_id, 'username')})"
    )

    await message.answer(f"Разбанен: {user_id}")

@router.message(SendPostState.waiting_post)
@new_user_handler
@track_activity
@is_admin
async def handle_post(message: Message, state: FSMContext, **kwargs):
    data = await state.get_data()

    # --- альбом ---
    if message.media_group_id:
        group = data.get("media_group", [])
        group.append(message)

        await state.update_data(media_group=group)

        await asyncio.sleep(1)

        data = await state.get_data()
        group = data.get("media_group")

        if not group:
            return

        asyncio.create_task(handle_send_ad(group, message.from_user.id))
        await state.clear()
        return

    # --- одиночное ---
    asyncio.create_task(handle_send_ad(message, message.from_user.id))
    await state.clear()

# #Добавление видиков. стоит вконце чтобы не попадать под рекламные посты
# @router.message(AdStateFilter("off"), lambda msg: msg.forward_origin)
# @is_admin
# async def new_video(message: Message, is_clb=False, **kwargs):
#     await message.reply("Рассылка сейчас выключена! Переключить режим рассылки можно здесь /ad")
#     return
 
# #Рекланые посты 
# @router.message(~AdStateFilter("off"), lambda msg: msg.forward_origin)
# @is_admin
# async def forward_handler(message: Message, is_clb=False, **kwargs):
#     user_id = message.chat.id if is_clb else message.from_user.id
    
#     if message:
#         asyncio.create_task(handle_send_ad(message, user_id))

@router.message()
@new_user_handler
@track_activity
@is_not_banned
async def fallback_handler(message: Message, **kwargs):
    if getattr(message, "pinned_message", None):
        return

    user_id = message.from_user.id
    is_activated = await UsersDatabase.get_value(user_id, 'is_activated')

    text = (message.text or "").strip()
    if text:
        codes = await CodesDatabase.get_by_code(text)
        if codes:
            code_id = codes[0][0]  # id is first column
            if is_activated == 1:
                await message.answer("Your access is already activated")
            else:
                await UsersDatabase.set_value(user_id, 'is_activated', 1)
                await UsersDatabase.set_value(user_id, 'last_code_used', text)
                await CodesDatabase.increment_applied_count(code_id)
                await message.answer(
                    LOCALES["activated successfully"],
                    parse_mode="HTML"
                )
                await send_currency_pairs_message(user_id)
                logger.info(f"Access activated for user {user_id} ({message.from_user.username}) with code: {text}")
            return
    if is_activated == 0:
        await message.answer(LOCALES["activate_access"], parse_mode="HTML")
    else:
        await message.answer("Unrecognized text.\n\nUse /signals to get trading signals or <b>contact me</b> directly<b>\n@Traderr_Lisa_not_bot</b>", parse_mode="HTML")



