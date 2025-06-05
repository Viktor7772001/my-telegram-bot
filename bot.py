# Импорты (добавляем Router!)
from aiogram import Bot, Dispatcher, types, Router, F
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

# Сохранение входящих сообщений
@router.message(F.content_type.in_({"text"}))
async def collect_messages(message: types.Message):
    global reminder_sent
    text = message.text or message.caption or ""
    if not text:
        return
    sender_id = (
        message.forward_from.id if message.forward_from else message.from_user.id
    )
    sender_name = (
        message.forward_from.full_name if message.forward_from else message.from_user.full_name
    )
    message_storage.add_message(
        Message(sender_id=sender_id, sender_name=sender_name, text=text, chat_id=message.chat.id)
    )
    if not reminder_sent:
        await message.answer(config.MERGE_REMINDER)
        reminder_sent = True


@router.message(Command("merge"))
async def handle_merge(message: types.Message):
    global reminder_sent
    if not message_storage.messages:
        await message.answer("Нет сообщений для объединения.")
        return
    parts = []
    for msg in message_storage.messages:
        name = message_storage.get_name(msg.sender_id, msg.sender_name)
        parts.append(f"{name}: {msg.text}")
    await message.answer("\n".join(parts))
    message_storage.clear()
    reminder_sent = False


@router.message(Command("clear"))
async def handle_clear(message: types.Message):
    global reminder_sent
    message_storage.clear()
    reminder_sent = False
    await message.answer("История очищена.")


@router.message(Command("rename"))
async def handle_rename(message: types.Message):
    first_id = message_storage.start_renaming(message.from_user.id)
    if first_id is None:
        await message.answer(config.RENAME_NO_PARTICIPANTS)
        return
    name = message_storage.get_name(first_id, "user")
    await message.answer(f"{config.RENAME_START}\nВведите новое имя для {name}:")


@router.message(lambda m: message_storage.is_renaming(m.from_user.id))
async def process_rename(message: types.Message):
    next_id = message_storage.record_name(message.from_user.id, message.text)
    if next_id is None:
        await message.answer("✅ Переименование завершено.")
    else:
        name = message_storage.get_name(next_id, "user")
        await message.answer(f"Введите новое имя для {name}:")


# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logger.info("Starting bot...")
    asyncio.run(main())
