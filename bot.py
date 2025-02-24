import logging
import os
import asyncio
router = Router()  
from aiogram import Bot, Dispatcher, types, Router  # Добавили Router
from aiogram.filters import Command  # Добавили для обработки команд

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import config
from storage import Message, MessageStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    logger.error("No token provided")
    exit(1)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()  # Оставляем диспетчер
dp.include_router(router)  # Подключаем роутер к диспетчеру 

# Инициализируем хранилище сообщений
message_storage = MessageStorage()
reminder_sent = False  # Флаг для отслеживания отправки напоминания

# Создаем клавиатуру с кнопкой "Старт"
start_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="🚀 Старт")]  # Кнопки передаются в виде списка списков
    ]
)


# Создаем объект для удаления клавиатуры
remove_keyboard = ReplyKeyboardRemove(remove_keyboard=True)


async def send_delayed_message(chat_id: int, delay: float = 2.0):
    """Отправить сообщение с задержкой"""
    logger.info(f"Scheduling delayed message for chat {chat_id}")
    await asyncio.sleep(delay)
    await bot.send_message(chat_id, config.MERGE_REMINDER, reply_markup=remove_keyboard)
    logger.info(f"Sent delayed reminder to chat {chat_id}")

async def show_available_commands(message: types.Message):
    """Показать список доступных команд"""
    logger.info(f"Showing available commands to user {message.from_user.id}")
    await message.answer("\n🤖 Доступные команды:\n" + config.HELP_MESSAGE, reply_markup=remove_keyboard)

@router.message(Command('start', 'help', 'restart'))  # Заменили @dp на @router + Command()
async def send_welcome(message: types.Message):
    """Обработчик команд /start, /help и /restart"""
    global reminder_sent
    user_id = message.from_user.id
    command = message.text
    logger.info(f"Received {command} command from user {user_id}")

    if message.text == '/start':
        await message.answer(config.WELCOME_MESSAGE, reply_markup=start_keyboard)
        logger.info(f"Sent welcome message to user {user_id}")
    elif message.text == '/restart':
        message_storage.clear()
        reminder_sent = False
        await message.answer(config.RESTART_MESSAGE, reply_markup=start_keyboard)
        logger.info(f"Restarted bot for user {user_id}, cleared storage")
    else:  # /help
        await message.answer(config.HELP_MESSAGE, reply_markup=remove_keyboard)
        logger.info(f"Sent help message to user {user_id}")

@router.message_handler(lambda message: message.text == "🚀 Старт")
async def handle_start_button(message: types.Message):
    """Обработчик нажатия кнопки Старт"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} pressed Start button")
    await message.answer(config.WELCOME_MESSAGE, reply_markup=remove_keyboard)
    logger.info(f"Sent welcome message after Start button to user {user_id}")

@router.message_handler(lambda message: message.text == '/rename')
async def rename_participants(message: types.Message):
    """Обработчик команды переименования участников"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    logger.info(f"User {user_id} requested to rename participants")

    if not message_storage.has_messages():
        await message.answer(config.RENAME_NO_PARTICIPANTS, reply_markup=remove_keyboard)
        logger.info(f"No messages to rename participants for user {user_id}")
        return

    # Начинаем процесс переименования
    first_participant = message_storage.start_rename_process(chat_id)
    if not first_participant:
        await message.answer(config.RENAME_NO_PARTICIPANTS, reply_markup=remove_keyboard)
        logger.info(f"No participants found for renaming for user {user_id}")
        return

    # Отправляем сообщение о начале процесса
    await message.answer(config.RENAME_START, reply_markup=remove_keyboard)
    # Спрашиваем про первого участника
    await message.answer(
        config.RENAME_ASK_CHANGE.format(first_participant[1]),
        reply_markup=remove_keyboard
    )
    logger.info(f"Started rename process for user {user_id}, active: {message_storage.is_rename_active(chat_id)}")

@router.message_handler(lambda message: message_storage.is_rename_active(message.chat.id))
async def process_rename(message: types.Message):
    """Обработчик ответов в процессе переименования"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    new_name = message.text
    logger.info(f"Processing rename response from user {user_id}: {new_name}")

    # Проверяем состояние переименования
    rename_state = message_storage.get_rename_state(chat_id)
    if not rename_state or not rename_state.active:
        logger.warning(f"Rename state not found or inactive for user {user_id}")
        return

    # Если пользователь хочет оставить текущее имя
    if new_name == '+':
        logger.info(f"User {user_id} chose to keep current name")
        # Получаем следующего участника
        next_participant = message_storage.get_next_participant(chat_id)
        if next_participant:
            # Если есть следующий участник, спрашиваем про него
            await message.answer(config.RENAME_NEXT, reply_markup=remove_keyboard)
            await message.answer(
                config.RENAME_ASK_CHANGE.format(next_participant[1]),
                reply_markup=remove_keyboard
            )
            logger.info(f"Moving to next participant for user {user_id}")
        else:
            # Если участников больше нет, показываем результат
            result = message_storage.get_merged_messages(chat_id)
            await message.answer(config.RENAME_COMPLETE, reply_markup=remove_keyboard)
            await message.answer(result, reply_markup=remove_keyboard)
            await show_available_commands(message)
            logger.info(f"Completed rename process for user {user_id}")
        return

    # Сохраняем новое имя
    if message_storage.rename_current_participant(chat_id, new_name):
        await message.answer(config.RENAME_SUCCESS, reply_markup=remove_keyboard)
        logger.info(f"Renamed participant to {new_name} for user {user_id}")

        # Получаем следующего участника
        next_participant = message_storage.get_next_participant(chat_id)
        if next_participant:
            # Если есть следующий участник, спрашиваем про него
            await message.answer(config.RENAME_NEXT, reply_markup=remove_keyboard)
            await message.answer(
                config.RENAME_ASK_CHANGE.format(next_participant[1]),
                reply_markup=remove_keyboard
            )
            logger.info(f"Moving to next participant for user {user_id}")
        else:
            # Если участников больше нет, показываем результат
            result = message_storage.get_merged_messages(chat_id)
            await message.answer(config.RENAME_COMPLETE, reply_markup=remove_keyboard)
            await message.answer(result, reply_markup=remove_keyboard)
            await show_available_commands(message)
            logger.info(f"Completed rename process for user {user_id}")

@router.message_handler(Command('continue'))
async def continue_adding(message: types.Message):
    """Продолжить добавление сообщений"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    logger.info(f"User {user_id} continuing to add messages")

    if not message_storage.has_chat_messages(chat_id):
        await message.answer(config.NO_MESSAGES, reply_markup=remove_keyboard)
        logger.info(f"No messages to continue for user {user_id}")
        return

    # Логируем текущее состояние сообщений и имён перед продолжением
    current_messages = message_storage.get_merged_messages(chat_id)
    logger.info(f"Current state before continue for chat {chat_id}:")
    logger.info(f"Messages:\n{current_messages}")
    logger.info(f"Custom names: {message_storage._custom_names}")

    # Если есть активное состояние переименования, очищаем его
    if message_storage.is_rename_active(chat_id):
        message_storage._rename_states.pop(chat_id, None)
        logger.info(f"Cleared rename state for chat {chat_id}")

    # Сохраняем текущий список сообщений и пользовательские имена
    global reminder_sent
    reminder_sent = False
    await message.answer(config.CONTINUE_MESSAGE, reply_markup=remove_keyboard)
    await asyncio.sleep(2)
    await bot.send_message(chat_id, config.MERGE_REMINDER, reply_markup=remove_keyboard)
    logger.info(f"Sent delayed reminder to chat {chat_id}")

@router.message()
async def handle_message(message: types.Message):
    """Обработчик всех остальных сообщений"""
    # Пропускаем сообщения, если активен процесс переименования
    if message_storage.is_rename_active(message.chat.id):
        return

    global reminder_sent
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.forward_from or message.forward_from_chat:
        logger.info(f"Received forwarded message from user {user_id}")
        # Определяем отправителя
        if message.forward_from:
            sender_id = message.forward_from.id
            sender_name = message_storage._custom_names.get(sender_id, message.forward_from.first_name)
        else:
            sender_id = message.forward_from_chat.id
            sender_name = message_storage._custom_names.get(sender_id, message.forward_from_chat.title)

        # Извлекаем текст или подпись к медиа
        text = message.text or message.caption
        if not text:
            text = "[медиа-файл]"

        # Создаем и сохраняем сообщение
        msg = Message(sender_id=sender_id, sender_name=sender_name, text=text, chat_id=chat_id)
        message_storage.add_message(msg)
        await message.answer(config.MESSAGE_ADDED, reply_markup=remove_keyboard)
        logger.info(f"Added message from {sender_name} to storage for user {user_id}")

        # Отправляем напоминание только если это первое сообщение
        if not reminder_sent:
            asyncio.create_task(send_delayed_message(chat_id))
            reminder_sent = True
            logger.info(f"Scheduled reminder for user {user_id}")

    elif message.text == "/merge":
        logger.info(f"User {user_id} requested to merge messages")
        if not message_storage.has_chat_messages(chat_id):
            await message.answer(config.NO_MESSAGES, reply_markup=remove_keyboard)
            logger.info(f"No messages to merge for user {user_id}")
            return

        # Получаем отформатированный текст
        result = message_storage.get_merged_messages(chat_id)
        await message.answer(result, reply_markup=remove_keyboard)
        logger.info(f"Sent merged messages to user {user_id}")

        # Показываем список команд
        await show_available_commands(message)

    else:
        # Не показываем сообщение об ошибке после команды /continue
        if message.text != "/continue":
            await message.answer(config.INVALID_MESSAGE, reply_markup=remove_keyboard)
            logger.info(f"Received invalid message from user {user_id}")

@router.message(Command('clear'))
async def clear_messages(message: types.Message):
    """Очистить сохраненные сообщения"""
    global reminder_sent
    user_id = message.from_user.id
    logger.info(f"Clearing messages for user {user_id}")

    message_storage.clear()
    reminder_sent = False
    await message.answer(config.MESSAGES_CLEARED, reply_markup=remove_keyboard)
    logger.info(f"Cleared all messages for user {user_id}")


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logger.info("Starting bot...")
    asyncio.run(main())
