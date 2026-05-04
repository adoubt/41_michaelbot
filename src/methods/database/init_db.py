import asyncio

from src.methods.database.users_manager import UsersDatabase
from src.methods.database.videos_manager import VideosDatabase
from src.methods.database.config_manager import ConfigDatabase
from src.methods.database.ads_manager import AdsDatabase
from src.methods.database.codes_manager import CodesDatabase
async def init_databases() -> None:
    await UsersDatabase.create_table()
    await ConfigDatabase.create_table()
    await CodesDatabase.create_table()
    await AdsDatabase.create_table()
    if await ConfigDatabase.get_value('ad_state') is None:
        await ConfigDatabase.set_value('ad_state','test')
    if await ConfigDatabase.get_value('inactive_ban_count') is None:
        await ConfigDatabase.set_value('inactive_ban_count', 0)
    
# # Пример вызова
# if __name__ == '__main__':
#     asyncio.run(init_databases())
