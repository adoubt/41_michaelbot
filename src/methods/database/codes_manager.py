import aiosqlite

DB_PATH = "src/databases/codes.db"


class CodesDatabase:
    @classmethod
    async def create_table(cls):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE,
                    applied_count INTEGER
                )
            ''')
            await db.commit()

    @classmethod
    async def add(cls, code: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                'INSERT INTO codes (code, applied_count) VALUES (?, ?)',
                (code, 0)
            )
            await db.commit()


    @classmethod
    async def get_by_code(cls, code: str):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                'SELECT * FROM codes WHERE code = ?',
                (code,)
            ) as cursor:
                return await cursor.fetchall()

    @classmethod
    async def delete_code(cls, code: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                'DELETE FROM codes WHERE code = ?',
                (code,)
            )
            await db.commit()

    @classmethod
    async def increment_applied_count(cls, code_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                'UPDATE codes SET applied_count = applied_count + 1 WHERE id = ?',
                (code_id,)
            )
            await db.commit()

    @classmethod
    async def get_all_codes(cls):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute('SELECT code, applied_count FROM codes') as cursor:
                return await cursor.fetchall()

    @classmethod
    async def get_code_id_by_code(cls, code: str):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                'SELECT id FROM codes WHERE code = ?',
                (code,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
