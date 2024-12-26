from database.methods import get_products, add_price_history
from utils.utils import fetch_product_details
from aiohttp import ClientSession
import time

async def track_prices(bot):
    start_time = time.time()
    print("Запуск отслеживания цен...")
    try:
        async with ClientSession() as session:
            users_products = {}
            all_products = await get_products()

            if not all_products:
                print("Нет товаров для отслеживания.")
                return

            for product in all_products:
                product_id, user_id, link, title, price_with_card, price_no_card, price_original = product
                details = fetch_product_details(link)
                print(f"Детали для {link}: {details}")

                new_price_with_card = details.get("price_with_card", price_with_card)
                new_price_no_card = details.get("price_no_card", price_no_card)
                new_price_original = details.get("price_original", price_original)

                if (
                    new_price_with_card != price_with_card or
                    new_price_no_card != price_no_card or
                    new_price_original != price_original
                ):
                    if user_id not in users_products:
                        users_products[user_id] = []
                    users_products[user_id].append((title, price_with_card, new_price_with_card,
                                                      price_no_card, new_price_no_card,
                                                      price_original, new_price_original,
                                                      link))

                await add_price_history(product_id, new_price_with_card, new_price_no_card, new_price_original)

            await notify_users(bot, users_products)

    except Exception as e:
        print(f"Ошибка в функции отслеживания цен: {e}")
    finally:
        print("Отслеживание цен завершено.")
        print(f"Время выполнения: {time.time() - start_time:.2f} секунд")

async def notify_users(bot, users_products):
    for user_id, products in users_products.items():
        message = "🔔 **Обновление цен:**\n"
        for (title, old_price_card, new_price_card,
             old_price_no_card, new_price_no_card,
             old_price_original, new_price_original, link) in products:
            message += (
                f"🔹 [{title}]({link})\n"
                f"Цена с картой Ozon: {old_price_card} → {new_price_card}\n"
                f"Цена без карты: {old_price_no_card} → {new_price_no_card}\n"
                f"Цена без скидки: {old_price_original} → {new_price_original}\n"
            )
        await bot.send_message(user_id, message, disable_web_page_preview=True)
