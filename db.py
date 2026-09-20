import aiosqlite

DB_PATH = "lifebot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                task TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                PRIMARY KEY(user_id, id)
            )
        """)
        await db.commit()

async def get_next_id(db, user_id: str, table: str) -> int:
    async with db.execute(
        f"SELECT id FROM {table} WHERE user_id = ? ORDER BY id",
        (user_id,)
    ) as cursor:
        rows = await cursor.fetchall()

    existing = {row[0] for row in rows}
    new_id = 1
    while new_id in existing:
        new_id += 1
    return new_id

async def add_todo(user_id: str, task: str):
    async with aiosqlite.connect(DB_PATH) as db:
        new_id = await get_next_id(db, user_id, "todos")
        
        await db.execute(
            "INSERT INTO todos (id, user_id, task) VALUES (?, ?, ?)",
            (new_id, user_id, task)
        )
        await db.commit()
        return new_id

async def list_todos(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, task, done FROM todos WHERE user_id = ? ORDER BY done, id",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

async def complete_todo(user_id: str, todo_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT done FROM todos WHERE user_id = ? AND id = ?",
            (user_id, todo_id)
        ) as cursor:
            row = await cursor.fetchone()

            if row is None:
                return "not_found"

            if row[0] == 1:
                return "already_done"
            
        await db.execute(
            "UPDATE todos SET done = 1 WHERE user_id = ? AND id = ?",
            (user_id, todo_id)
        )
        await db.commit()
        return "complete"

async def delete_todo(user_id: str, todo_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT task FROM todos WHERE user_id = ? AND id = ?",
            (user_id, todo_id)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None

        task = row[0]
        
        await db.execute(
            "DELETE FROM todos WHERE user_id = ? AND id = ?",
            (user_id, todo_id)
        )
        await db.commit()
        return task

async def add_reminder(user_id: str, message: str, remind_at: str):
    async with aiosqlite.connect(DB_PATH) as db:
        new_id = await get_next_id(db, user_id, "reminders")
        await db.execute(
            "INSERT INTO reminders (id, user_id, message, remind_at) VALUES (?, ?, ?, ?)",
            (new_id, user_id, message, remind_at)
        )
        await db.commit()
        return new_id

async def get_due_reminders(user_id: str, message: str, remind_at: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, user_id, message FROM reminders WHERE remind_at <= DATETIME('now')"
        ) as cursor:
            return await cursor.fetchall()

async def delete_reminder(reminder_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        await db.commit()