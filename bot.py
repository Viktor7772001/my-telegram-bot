# Импорты (добавляем Router!)
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
import logging
import os
import asyncio
from config import config
from storage import Message, MessageStorage

# Создаем Router (маршрутизатор)
router = Router()

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (получите у @BotFather)
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    logger.error("No token provided")
    exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
dp.include_router(router)  # Подключаем роутер

# Хранилище сообщений
message_storage = MessageStorage()
reminder_sent = False

# Создаем клавиатуру (новый синтаксис!)
start_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🚀 Старт")]
    ],
    resize_keyboard=True
)

# Удаление клавиатуры
remove_keyboard = types.ReplyKeyboardRemove()

# Обработчик /start, /help, /restart
@router.message(Command('start', 'help', 'restart'))
async def send_welcome(message: types.Message):
    global reminder_sent
    user_id = message.from_user.id
    command = message.text

    if command == '/start':
        await message.answer(config.WELCOME_MESSAGE, reply_markup=start_keyboard)
    elif command == '/restart':
        message_storage.clear()
        reminder_sent = False
        await message.answer(config.RESTART_MESSAGE, reply_markup=start_keyboard)
    else:
        await message.answer(config.HELP_MESSAGE, reply_markup=remove_keyboard)

# Обработчик кнопки "Старт"
@router.message(lambda message: message.text == "🚀 Старт")
async def handle_start_button(message: types.Message):
    await message.answer(config.WELCOME_MESSAGE, reply_markup=remove_keyboard)

# ... (остальные обработчики из вашего кода, заменив @dp на @router)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logger.info("Starting bot...")
    asyncio.run(main())
