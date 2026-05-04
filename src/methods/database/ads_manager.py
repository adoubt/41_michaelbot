import aiosqlite

DB_PATH = "src/databases/ads.db"


class AdsDatabase:
    @classmethod
    async def create_table(cls):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ads_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad_id INTEGER,
                    user_id INTEGER,
                    message_id INTEGER
                )
            ''')
            await db.commit()

    @classmethod
    async def add(cls, ad_id: int, user_id: int, message_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                'INSERT INTO ads_messages (ad_id, user_id, message_id) VALUES (?, ?, ?)',
                (ad_id, user_id, message_id)
            )
            await db.commit()

    @classmethod
    async def add_many(cls, ad_id: int, user_id: int, message_ids: list[int]):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.executemany(
                'INSERT INTO ads_messages (ad_id, user_id, message_id) VALUES (?, ?, ?)',
                [(ad_id, user_id, mid) for mid in message_ids]
            )
            await db.commit()

    @classmethod
    async def get_by_ad(cls, ad_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                'SELECT user_id, message_id FROM ads_messages WHERE ad_id = ?',
                (ad_id,)
            ) as cursor:
                return await cursor.fetchall()

    @classmethod
    async def delete_ad(cls, ad_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                'DELETE FROM ads_messages WHERE ad_id = ?',
                (ad_id,)
            )
            await db.commit()

    @classmethod
    async def get_ads_ids(cls):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                'SELECT DISTINCT ad_id FROM ads_messages'
            ) as cursor:
                return [row[0] for row in await cursor.fetchall()]