from datetime import datetime
import aiosqlite

async def init_db():
    async with aiosqlite.connect("database.db") as db:
        # Таблица пользователей
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT
        )
        """)

        # Таблица товаров
        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            link TEXT,
            title TEXT,
            price_with_card TEXT,
            price_no_card TEXT,
            price_original TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # Таблица истории изменения цен
        await db.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            datetime TEXT,
            price_with_card TEXT,
            price_no_card TEXT,
            price_original TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)
        await db.commit()

async def add_user(user_id: int, username: str):
    async with aiosqlite.connect("database.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
        await db.commit()


async def add_product_to_db(user_id: int, title: str, link: str, price_with_card: str, price_no_card: str, price_original: str):
    async with aiosqlite.connect("database.db") as db:
        print(f"Попытка добавить товар: {title}, {link}, {price_with_card} для пользователя {user_id}.")  # Отладка
        query = """
            INSERT INTO products (user_id, title, link, price_with_card, price_no_card, price_original) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        result = await db.execute(query, (user_id, title, link, price_with_card, price_no_card, price_original))
        product_id = result.lastrowid  # Получение ID нового товара

        try:
            # Занесение данных в таблицу истории изменения цены
            await db.execute("""
                INSERT INTO price_history (product_id, datetime, price_with_card, price_no_card, price_original) 
                VALUES (?, datetime('now'), ?, ?, ?)
            """, (product_id, price_with_card, price_no_card, price_original))
            await db.commit()
        except Exception as e:
            print(f"Ошибка при добавлении записи в price_history: {e}")
            await db.rollback()  # Откат в случае ошибки

        print(f"Товар добавлен. Новый ID: {product_id}.")  # Отладка
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        print(await cursor.fetchall())  # Проверяем, добавлен ли товар
        return product_id


async def remove_product_from_db(product_id: int):
    async with aiosqlite.connect("database.db") as db:
        await db.execute("DELETE FROM price_history WHERE product_id = ?", (product_id,))
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()

async def get_products(user_id: int = None):
    async with aiosqlite.connect("database.db") as db:
        if user_id is None:
            cursor = await db.execute(""" 
                SELECT id, user_id, link, title, price_with_card, price_no_card, price_original 
                FROM products
            """)
        else:
            cursor = await db.execute(""" 
                SELECT id, user_id, link, title, price_with_card, price_no_card, price_original 
                FROM products WHERE user_id = ?
            """, (user_id,))
        return await cursor.fetchall()


async def update_price(product_id: int, new_price: str):
    async with aiosqlite.connect("database.db") as db:
        await db.execute("""
        UPDATE products SET price_with_card = ? WHERE id = ?
        """, (new_price, product_id))
        await db.commit()

async def add_price_history(product_id: int, price_with_card: str, price_no_card: str, price_original: str):
    async with aiosqlite.connect("database.db") as db:
        datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute("""
        INSERT INTO price_history (product_id, datetime, price_with_card, price_no_card, price_original)
        VALUES (?, ?, ?, ?, ?)
        """, (product_id, datetime_now, price_with_card, price_no_card, price_original))
        await db.commit()


async def update_product_price(product_id: int, new_price_with_card: str, new_price_no_card: str,
                               new_price_original: str):
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute(""" 
        SELECT price_with_card, price_no_card, price_original FROM products WHERE id = ? 
        """, (product_id,))
        current_price, current_price_no_card, current_price_original = await cursor.fetchone()

        # Проверяем изменение цен
        if (new_price_with_card != current_price or
                new_price_no_card != current_price_no_card or
                new_price_original != current_price_original):
            # Обновляем таблицу истории
            await add_price_history(product_id, new_price_with_card, new_price_no_card, new_price_original)

            # Обновляем текущие цены в таблице products
            await db.execute("""
                UPDATE products
                SET price_with_card = ?, price_no_card = ?, price_original = ?
                WHERE id = ?
            """, (new_price_with_card, new_price_no_card, new_price_original, product_id))
            await db.commit()

            return True  # Указывает, что цена изменилась
        return False

async def get_product_by_id(product_id: int):
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return await cursor.fetchone()  # Вернёт None, если товар не найден

async def get_price_history(product_id: int):
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute("""
            SELECT * FROM price_history WHERE product_id = ? ORDER BY datetime DESC
        """, (product_id,))
        return await cursor.fetchall()  # Вернёт пустой список, если истории нет