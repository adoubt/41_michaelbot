import asyncio
from datetime import datetime, timedelta
from loguru import logger
from src.methods.database.users_manager import UsersDatabase
from src.methods.database.config_manager import ConfigDatabase
from src.methods.utils import ban_user
from src.misc import (
    INACTIVE_BAN_THRESHOLD_SECONDS,
    BANNED_NOTIFY_THRESHOLD_SECONDS,
    USER_MANAGEMENT_LOOP_INTERVAL_SECONDS,
)

async def ban_inactive_users():
    """Банит пользователей, которые неактивны более INACTIVE_BAN_THRESHOLD_SECONDS."""
    users = await UsersDatabase.get_all()
    now = datetime.now()
    threshold = now - timedelta(seconds=INACTIVE_BAN_THRESHOLD_SECONDS)

    blocked_count = 0
    for user in users:
        user_id = user[0]  # user_id
        is_banned = user[23]  # is_banned
        is_admin = user[10]  # is_admin
        last_activity_str = user[13]  # last_activity_at
        is_activated = user[11]  # is_activated
        if is_admin:
            continue
        if not is_activated:
            continue
        if not is_banned and last_activity_str:
            last_activity = datetime.fromisoformat(last_activity_str)
            if last_activity < threshold:
                await ban_user(user_id)
                blocked_count += 1

    if blocked_count > 0:
        # Update the inactive ban count in config
        current_count = await ConfigDatabase.get_value('inactive_ban_count') or 0
        await ConfigDatabase.set_value('inactive_ban_count', int(current_count) + blocked_count)
        logger.info(f"Inactive ban: blocked {blocked_count} users")


async def notify_already_banned_users():
    """Повторно уведомляет/банит уже забаненных пользователей, если прошло >10 секунд после последнего уведомления."""
    users = await UsersDatabase.get_all()
    now = datetime.now()

    notify_count = 0
    for user in users:
        user_id = user[0]
        is_banned = user[23]
        is_admin = user[10]
        last_notify_str = user[14]  # last_block_notify_at

        if is_admin:
            continue

        if is_banned and last_notify_str:
            last_notify = datetime.fromisoformat(last_notify_str)
            if now - last_notify > timedelta(seconds=BANNED_NOTIFY_THRESHOLD_SECONDS):
                await ban_user(user_id)
                notify_count += 1

    if notify_count > 0:
        logger.info(f"Banned notify: re-sent ban to {notify_count} users")


async def user_management_loop():
    """Бесконечный цикл для управления пользователями каждые USER_MANAGEMENT_LOOP_INTERVAL_SECONDS."""
    while True:
        await ban_inactive_users()
        await notify_already_banned_users()
        await asyncio.sleep(USER_MANAGEMENT_LOOP_INTERVAL_SECONDS)