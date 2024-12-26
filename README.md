# Telegram Price Tracker Bot

## Описание
Telegram-бот для отслеживания цен на товары с Ozon. Пользователи могут добавлять товары для мониторинга, удалять их, просматривать текущий список товаров и историю изменений цен. Бот автоматически парсит информацию о товарах с сайта Ozon.

## Возможности
- Добавление товаров для отслеживания через ссылки.
- Удаление товаров из списка по ID (возможность удаления нескольких товаров одновременно).
- Просмотр списка добавленных товаров с текущими ценами.
- Просмотр истории изменения цен на товары.
- Интуитивно понятное управление через меню и команды.

## Технологии
- **Aiogram**: Фреймворк для работы с Telegram Bot API.
- **Selenium**: Используется для парсинга данных о товарах с сайта Ozon.
- **SQLite**: Хранение данных о пользователях, товарах и ценах.

## Установка и настройка

1. Склонируйте репозиторий:
    ```bash
    git clone <URL>
    cd telegram-price-tracker-bot
    ```

2. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

3. Настройте бота:
    - Создайте файл `config.py` в папке `config_data/`.
    - Укажите токен бота и другие настройки:
      ```python
      BOT_TOKEN = "Ваш токен Telegram Bot API"
      ```

4. Запустите бота:
    ```bash
    python main.py
    ```

## Основные команды
- `/start`: Перезапуск бота.
- **Добавить товар**: Добавление товара для отслеживания.
- **Удалить товар**: Удаление товара из списка (возможность удаления нескольких товаров).
- **Список товаров**: Просмотр всех добавленных товаров.
- **История цен**: Просмотр истории изменения цен на выбранный товар.
- **Помощь**: Получение справки по боту.
- **О боте**: Информация о функционале бота.

## Основные файлы

### `handlers.py`
Содержит основную логику обработки команд и взаимодействия с пользователем.

### `database/database.py`
Реализует взаимодействие с базой данных, включая добавление, удаление и получение данных.

### `utils/utils.py`
Содержит вспомогательные функции, включая парсинг данных о товарах с помощью Selenium.

### `main.py`
Точка входа для запуска бота.

## Пример использования
1. Добавление товара:
    - Отправьте ссылку на товар в ответ на запрос.
    - Бот сохранит товар и предоставит информацию о текущих ценах.

2. Удаление товаров:
    - Используйте команду "Удалить товар".
    - Введите ID одного или нескольких товаров через пробел или запятую.

3. Просмотр истории цен:
    - Используйте команду "История цен".
    - Выберите товар по ID из списка.

## Будущие улучшения
- Уведомления об изменении цен.
- Поддержка других платформ.
- Более сложный анализ данных о ценах.

---

Если у вас есть вопросы или предложения, не стесняйтесь открывать issue в репозитории!