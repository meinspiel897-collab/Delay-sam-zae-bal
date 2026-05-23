import os
import logging
import asyncio
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования на вывод в sys.stdout для логов Render
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Токен берем из переменных окружения
API_TOKEN = os.getenv("TOKEN")
if not API_TOKEN:
    logger.error("КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения 'TOKEN' отсутствует в настройках Render!")
    sys.exit(1)

# Порт для Render Web Service (Render автоматически передает переменную PORT)
PORT = int(os.getenv("PORT", "10000"))

# Инициализируем бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ID стикера кита и ссылки
WHALE_STICKER_ID = "CAACAgEAAxkBAAFKV1RqEF_JacpzbFDVm0tHXYhFeNMFegACGwMAArAHGESRLvZwzZJ9sjsE"
OFFICIAL_CHANNEL_URL = "https://t.me/samosoboy_official"
MINI_APP_URL = "https://t.me/samosoboy_bot/app"  # Ссылка на Mini App

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_health_check(request):
    return web.Response(text="Бот СамоСобой запущен и работает успешно!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    app.router.add_get('/healthz', handle_health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"Здоровье Web-сервиса успешно запущено на порту {PORT}")

# --- КЛАВИАТУРЫ ОПРОСА ---

def get_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎣 Начать отлавливать", callback_data="step_1")
    return builder.as_markup()

def get_step_1_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="1-3", callback_data="step_2")
    builder.button(text="3-5", callback_data="step_2")
    builder.button(text="5-7", callback_data="step_2")
    builder.button(text="Я не хочу", callback_data="step_2")
    builder.adjust(1)
    return builder.as_markup()

def get_step_2_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="9-13", callback_data="step_3")
    builder.button(text="13-15", callback_data="step_3")
    builder.button(text="16-18", callback_data="step_3")
    builder.button(text="18 и старше", callback_data="step_3")
    builder.button(text="Не имеет значения", callback_data="step_3")
    builder.adjust(1)
    return builder.as_markup()

def get_step_3_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Подписаться", url=OFFICIAL_CHANNEL_URL)
    builder.button(text="🏁 Завершить", callback_data="finish")
    builder.adjust(1)
    return builder.as_markup()

def get_final_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⛵️ Отправить кораблик", callback_data="send_boat")
    builder.button(text="📱 Открыть приложение", web_app=types.WebAppInfo(url=MINI_APP_URL))
    builder.adjust(1)
    return builder.as_markup()

# --- ОБРАБОТЧИКИ СОБЫТИЙ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Рады видеть тебя на борту. **СамоСобой** — это уютный океан, "
        "куда люди запускают свои мысли на бумажных корабликах.\n\n"
        "Давай быстро настроим твой радар."
    )
    await message.answer(
        welcome_text, 
        reply_markup=get_start_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "step_1")
async def process_step_1(callback: types.CallbackQuery):
    step_1_text = (
        "*Шаг 1*\n\n"
        "Сколько корабликов в час вы хотели бы получать от других пользователей, находясь оффлайн?"
    )
    await callback.message.edit_text(
        text=step_1_text,
        reply_markup=get_step_1_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "step_2")
async def process_step_2(callback: types.CallbackQuery):
    step_2_text = (
        "*Шаг 2*\n\n"
        "Вы бы хотели получать кораблики от людей определенного возраста?"
    )
    await callback.message.edit_text(
        text=step_2_text,
        reply_markup=get_step_2_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "step_3")
async def process_step_3(callback: types.CallbackQuery):
    step_3_text = (
        "*Шаг 3*\n\n"
        "Вы бы хотели подписаться на канал бота, чтобы не пропускать важные обновления, опросы и новости?"
    )
    await callback.message.edit_text(
        text=step_3_text,
        reply_markup=get_step_3_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "finish")
async def process_finish(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    first_name = callback.from_user.first_name
    
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Не удалось удалить сообщение: {e}")
        
    await callback.answer()

    try:
        await bot.send_sticker(chat_id=chat_id, sticker=WHALE_STICKER_ID)
    except Exception as e:
        logger.error(f"Не удалось отправить стикер: {e}")

    final_text = (
        f"*Добро пожаловать, {first_name}!*\n\n"
        "Отправьте свой первый кораблик в плавание через приложение или с помощью бота, если нет сети. "
        "Пожалуйста, будьте добры и не оставляйте слишком личную информацию."
    )
    
    await bot.send_message(
        chat_id=chat_id,
        text=final_text,
        reply_markup=get_final_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "send_boat")
async def process_send_boat(callback: types.CallbackQuery):
    await callback.message.answer(
        "Напишите текст вашей мысли (до 280 символов), и я отправлю её в плавание. ⛵️"
    )
    await callback.answer()

# --- КОРРЕКТНЫЙ ЗАПУСК ДВУХ СЕРВИСОВ ---

async def main():
    logger.info("Запуск инициализации приложения...")
    # 1. Запускаем фоновый веб-сервер для прохождения пинга от Render
    await start_web_server()
    
    # 2. Сбрасываем старые вебхуки Telegram во избежание конфликтов лонг-поллинга
    logger.info("Сброс вебхуков Telegram...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 3. Запускаем опрос сообщений бота
    logger.info("Бот начинает опрос серверов Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
    except Exception as e:
        logger.critical(f"Критическая ошибка при работе приложения: {e}", exc_info=True)
        sys.exit(2)
