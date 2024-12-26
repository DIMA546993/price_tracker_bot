import re
from aiogram import Router, types, F
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database.methods import add_user, add_product_to_db, remove_product_from_db, get_products, get_product_by_id, \
    get_price_history
from utils.utils import fetch_product_details

router = Router()

async def set_bot_commands(bot):
    commands = [
        BotCommand(command="/start", description="Перезапуск бота")
    ]
    await bot.set_my_commands(commands)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Добавить товар'), KeyboardButton(text='Удалить товар')],
        [KeyboardButton(text='Список товаров'), KeyboardButton(text='История цен')],
        [KeyboardButton(text='Помощь'), KeyboardButton(text='О боте')]
    ],
    resize_keyboard=True
)

def inline_delete_button(product_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🗑 Удалить товар', callback_data=f'delete_{product_id}')]
        ]
    )

class PriceHistoryStates(StatesGroup):
    waiting_for_product_id = State()

class AddProductStates(StatesGroup):
    waiting_for_links = State()

class RemoveProductStates(StatesGroup):
    waiting_for_product_id = State()

@router.message(F.text == '/start')
async def send_welcome(message: types.Message):
    await add_user(message.from_user.id, message.from_user.username)
    await message.reply("👋 Добро пожаловать в бота для отслеживания цен! \n\n"
                        "🛍️ Используйте меню ниже, чтобы начать.", reply_markup=main_menu)

@router.message(F.text == "Добавить товар")
async def add_product_start(message: types.Message, state: FSMContext):
    await message.answer("🔍 Пожалуйста, отправьте ссылку на товар для добавления.")
    await state.set_state(AddProductStates.waiting_for_links)

@router.message(AddProductStates.waiting_for_links)
async def process_links(message: types.Message, state: FSMContext):
    links = re.split(r'[,\s]+', message.text.strip())
    added_products = []

    for link in links:
        if not link.startswith("https://www.ozon.ru"):
            await message.answer(f"❌ Ссылка {link} не принадлежит Ozon. Проверьте её и попробуйте снова.")
            continue

        details = fetch_product_details(link)
        if "error" in details:
            await message.answer(f"❌ Ошибка при обработке ссылки: {link}")
            continue

        # Получаем данные о товаре
        title = details.get("title", "Без названия")
        price_with_card = details.get("price_with_card", "N/A")
        price_no_card = details.get("price_no_card", price_with_card)
        price_original = details.get("price_original", price_with_card)

        # Добавляем товар в базу данных
        product_id = await add_product_to_db(
            user_id=message.from_user.id,
            title=title,
            link=link,
            price_with_card=price_with_card,
            price_no_card=price_no_card,
            price_original=price_original
        )
        added_products.append((product_id, title, price_with_card, price_no_card, price_original))

    if added_products:
        response = "✅ Добавленные товары:\n\n"
        for _, title, price_with_card, price_no_card, price_original in added_products:
            response += (
                f"🔸 **Название**: {title}\n"
                f"💳 **Цена с картой**: {price_with_card}\n"
                f"💵 **Цена без карты**: {price_no_card}\n"
                f"💲 **Цена без скидки**: {price_original}\n\n"
            )
        await message.answer(response)
    else:
        await message.answer("⚠️ Не удалось добавить товары. Проверьте ссылки.")

    await state.clear()

@router.message(F.text == "Удалить товар")
async def remove_product_start(message: types.Message, state: FSMContext):
    products = await get_products(message.from_user.id)  # Получаем список товаров пользователя
    if not products:  # Проверяем, есть ли вообще товары
        await message.answer("📦 У вас нет добавленных товаров.")  # Сообщение, если товаров нет
        return

    # Формируем ответ с перечислением товаров и их ID
    response = "Ваши товары (ID - название):\n\n"
    for product in products:
        product_id, _, _, title, _, _, _ = product  # Извлекаем только нужные поля
        response += f"🔹 **ID**: {product_id} - {title}\n"  # Добавляем строку с ID и названием

    # Отправляем пользователю список товаров
    await message.answer(response)
    await message.answer("🗑️ Введите ID товара(ов), которые хотите удалить, через пробел или запятую.")  # Инструкция для ввода ID
    await state.set_state(RemoveProductStates.waiting_for_product_id)  # Переключаем FSM в состояние ожидания ID

@router.message(RemoveProductStates.waiting_for_product_id)
async def process_remove_product(message: types.Message, state: FSMContext):
    ids = re.split(r'[,\s]+', message.text.strip())  # Разделяем введенные ID по запятой или пробелу
    deleted_products = []

    for id_str in ids:
        try:
            product_id = int(id_str)  # Пробуем преобразовать ID в число
            await message.answer(f"🗑️ Попытка удалить товар с ID **{product_id}**.")  # Отладка

            # Проверяем наличие товара в базе данных
            product = await get_product_by_id(product_id)  # Функция, которая возвращает продукт по ID

            if product:  # Если товар найден
                await remove_product_from_db(product_id)
                deleted_products.append(product_id)  # Добавляем ID в список удалённых товаров
            else:
                await message.answer(f"❌ Не удалось найти товар с ID **{product_id}**. Пожалуйста, проверьте ваш список товаров.")

        except ValueError:
            await message.answer(f"⚠️ ID '{id_str}' не является числом.")

    if deleted_products:
        await message.answer(f"✅ Товары с ID **{', '.join(map(str, deleted_products))}** успешно удалены.")
    else:
        await message.answer("⚠️ Не удалось удалить ни один товар.")

    await state.clear()

@router.message(F.text == "Список товаров")
async def list_products(message: types.Message):
    products = await get_products(message.from_user.id)
    if not products:
        await message.answer("📦 У вас нет добавленных товаров.")
        return

    response = "Ваши товары:\n\n"
    for product_id, user_id, link, title, price_with_card, price_no_card, price_original in products:
        response += (
            f"🔹 **ID**: {product_id}\n"
            f"🔸 **Название**: [{title}]({link})\n"
            f"💳 **Цена с картой**: {price_with_card}\n"
            f"💵 **Цена без карты**: {price_no_card}\n"
            f"💲 **Цена без скидки**: {price_original}\n\n"
        )
    await message.answer(response, disable_web_page_preview=True)

@router.message(F.text == "История цен")
async def price_history_start(message: types.Message, state: FSMContext):
    products = await get_products(message.from_user.id)  # Получаем список товаров пользователя
    if not products:  # Проверяем, есть ли вообще товары
        await message.answer("📦 У вас нет добавленных товаров.")  # Сообщение, если товаров нет
        return

    # Формируем ответ с перечислением товаров и их ID
    response = "Ваши товары (ID - название):\n\n"
    for product in products:
        product_id, _, _, title, _, _, _ = product  # Извлекаем только нужные поля
        response += f"🔹 **ID**: {product_id} - {title}\n"  # Добавляем строку с ID и названием

    # Отправляем пользователю список товаров
    await message.answer(response)
    await message.answer("🔍 Введите ID товара, для которого хотите посмотреть историю цен.")  # Инструкция для ввода ID
    await state.set_state(PriceHistoryStates.waiting_for_product_id)  # Переключаем FSM в состояние ожидания ID

@router.message(PriceHistoryStates.waiting_for_product_id)
async def process_price_history_request(message: types.Message, state: FSMContext):
    try:
        product_id = int(message.text.strip())
        await message.answer(f"🔍 Запрашиваю историю цен для товара с ID **{product_id}**.")  # Отладка

        # Проверяем наличие товара в базе данных
        product = await get_product_by_id(product_id)  # Функция, которая возвращает продукт по ID

        if product:  # Если товар найден
            price_history = await get_price_history(product_id)  # Получаем историю цен
            if not price_history:
                await message.answer(f"❌ Нет истории цен для товара с ID **{product_id}**.")
                return

            response = "📈 История изменения цен:\n\n"
            for record in price_history:
                _, _, datetime, price_with_card, price_no_card, price_original = record
                response += (
                    f"📅 **Дата**: {datetime}\n"
                    f"💳 **Цена с картой**: {price_with_card}\n"
                    f"💵 **Цена без карты**: {price_no_card}\n"
                    f"💲 **Цена без скидки**: {price_original}\n\n"
                )
            await message.answer(response)
        else:
            await message.answer(f"❌ Не удалось найти товар с ID **{product_id}**. Пожалуйста, проверьте ваш список товаров.")

    except ValueError:
        await message.answer("⚠️ ID товара должен быть числом. Попробуйте снова.")
    finally:
        await state.clear()

@router.message(F.text == "Помощь")
async def help_message(message: types.Message):
    help_text = (
        "💡 *Команды бота:*\n\n"
        "1. /start - Запуск бота.\n"
        "2. Список товаров - Просмотреть все добавленные товары.\n"
        "3. Добавить товар - Добавить новый товар для отслеживания.\n"
        "4. История цен - Просмотреть историю цен на добавленные товары.\n"
        "5. Удалить товар - Удалить товар из списка.\n"
        "6. Помощь - Получить справку по командам."
    )
    await message.answer(help_text)

@router.message(F.text == "О боте")
async def about_command(message: types.Message):
    await message.answer("ℹ️ **О боте**:\n\n"
                         "Бот для отслеживания цен на товары с Ozon. "
                         "Вы можете добавлять товары, отслеживать изменения цен и получать уведомления.")