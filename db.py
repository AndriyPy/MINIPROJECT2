import aiosqlite

SQLITE_DB_NAME = "mini2.db"


async def create_tables():
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        cursor: aiosqlite.Cursor = await connection.cursor()

        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Users(
                   id           INTEGER PRIMARY KEY AUTOINCREMENT,
                   name         VARCHAR(30) NOT NULL,
                   email        VARCHAR(30) NOT NULL,
                   created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        await cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS Posts(
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    title       VARCHAR(30) NOT NULL,
                    description VARCHAR(300) NOT NULL,
                    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES Users(id) ON DELETE CASCADE
                );
            """
        )

        await connection.commit()
        await connection.close()


async def get_db():
    async with aiosqlite.connect(SQLITE_DB_NAME) as connection:
        connection.row_factory = aiosqlite.Row
        yield connection

        await connection.close()
