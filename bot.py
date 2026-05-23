import os
import logging
import asyncio
import threading
import html
from flask import Flask, send_from_directory
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка детального логирования
logging.basicConfig(level=logging.INFO)

# Получаем токен из переменных окружения Render
API_TOKEN = os.getenv("TOKEN")
if not API_TOKEN:
    raise ValueError("Переменная окружения TOKEN не найдена!")

# Инициализируем бота и диспетчер aiogram
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Данные для бота
WHALE_STICKER_ID = "CAACAgEAAxkBAAFKV1RqEF_JacpzbFDVm0tHXYhFeNMFegACGwMAArAHGESRLvZwzZJ9sjsE"
OFFICIAL_CHANNEL_URL = "https://t.me/samosoboy_official"

# Указываем адрес твоего Mini App.
# ВАЖНО: Telegram строго требует HTTPS-протокол. 
# Мы настроили Flask так, что он раздает созданный нами index.html.
# На Render твой домен будет иметь вид: https://<твое-имя-на-рендер>.onrender.com
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://delay-sam-zae-bal.onrender.com")
MINI_APP_URL = RENDER_EXTERNAL_URL  # Теперь кнопка будет открывать этот же веб-сервис на Render!

# --- НАСТРОЙКА FLASK СЕРВЕРА ДЛЯ RENDER WEB SERVICE ---
# Flask теперь не просто держит порт, а отдает красивый index.html для твоего Mini App!
flask_app = Flask(__name__, static_folder='.')

@flask_app.route('/')
def home():
    # Отдаем файл index.html, который лежит в той же папке
    return send_from_directory('.', 'index.html')

@flask_app.route('/healthz')
def healthz():
    return "OK", 200

def run_flask():
    port = int(os.getenv("PORT", "10000"))
    logging.info(f"Запуск Flask-сервера на порту {port}...")
    flask_app.run(host="0.0.0.0", port=port)

# --- КЛАВИАТУРЫ И ШАГИ ОПРОСА ---

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
    builder.adjust(1)  # Кнопки в столбик, по одной в ряду
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
    # Две кнопки в один ряд
    builder.button(text="⛵️ Отправить кораблик", callback_data="send_boat")
    builder.button(text="📱 Открыть приложение", web_app=types.WebAppInfo(url=MINI_APP_URL))
    builder.adjust(2)
    return builder.as_markup()

# --- ОБРАБОТЧИКИ СОБЫТИЙ БОТА ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    safe_name = html.escape(message.from_user.first_name or "Путешественник")
    welcome_text = (
        f"Привет, {safe_name}! 👋\n\n"
        "Рады видеть тебя на борту! <b>СамоСобой</b> — это уютный океан, "
        "куда люди запускают свои мысли на корабликах, отправляя их анонимно и на произвол судьбы.\n\n"
        "Давай прежде всего настроим твой радар, это не займет больше минуты."
    )
    await message.answer(
        welcome_text, 
        reply_markup=get_start_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "step_1")
async def process_step_1(callback: types.CallbackQuery):
    step_1_text = (
        "<b>Шаг 1</b>\n\n"
        "Сколько корабликов в час ты бы хотел получать от других пользователей, находясь оффлайн?"
    )
    await callback.message.edit_text(
        text=step_1_text,
        reply_markup=get_step_1_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "step_2")
async def process_step_2(callback: types.CallbackQuery):
    step_2_text = (
        "<b>Шаг 2</b>\n\n"
        "Ты бы хотел получать кораблики от людей определенного возраста?"
    )
    await callback.message.edit_text(
        text=step_2_text,
        reply_markup=get_step_2_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "step_3")
async def process_step_3(callback: types.CallbackQuery):
    step_3_text = (
        "<b>Шаг 3</b>\n\n"
        "Ты бы хотел подписаться на канал бота, чтобы не пропускать важные обновления, опросы и новости?"
    )
    await callback.message.edit_text(
        text=step_3_text,
        reply_markup=get_step_3_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "finish")
async def process_finish(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    # Безопасное имя пользователя
    safe_name = html.escape(callback.from_user.first_name or "Друг")
    
    # Подтверждаем клик немедленно, чтобы кнопка перестала "часиться"
    await callback.answer()

    # 1. Удаляем текущее сообщение опроса
    try:
        await callback.message.delete()
    except Exception as e:
        logging.error(f"Не удалось удалить сообщение: {e}")
        
    # 2. Отправляем стикер кита
    try:
        await bot.send_sticker(chat_id=chat_id, sticker=WHALE_STICKER_ID)
    except Exception as e:
        logging.error(f"Не удалось отправить стикер: {e}")

    # 3. Делаем небольшую паузу
    await asyncio.sleep(0.5)

    # 4. Финальный текст
    final_text = (
        f"С регистрацией, {safe_name}! 🎉\n\n"
        "Отправь свой первый кораблик в плавание через приложение или с помощью бота, если так удобнее 😉\n\n"
        "Пожалуйста, будь добр и не оставляй слишком личную информацию. "
        "Также рекомендуем ознакомиться со списком команд:\n\n"
        "▎ /start - приветствие новичков и меню\n"
        "▎ /catch - выловить чей-нибудь кораблик\n"
        "▎ /profile - твой профиль"
    )
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=final_text,
            reply_markup=get_final_keyboard(),
            parse_mode="HTML"
        )
        logging.info("Финальное приветственное сообщение успешно отправлено.")
    except Exception as e:
        logging.error(f"КРИТИЧЕСКАЯ ОШИБКА ОТПРАВКИ СООБЩЕНИЯ: {e}")

@dp.callback_query(F.data == "send_boat")
async def process_send_boat(callback: types.CallbackQuery):
    await callback.message.answer(
        "Напиши текст твоей мысли (до 280 символов), и я отправлю её в плавание. ⛵️"
    )
    await callback.answer()

# --- ОСНОВНОЙ ЗАПУСК ---

async def main():
    # Запускаем Flask в отдельном фоновом потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Сбрасываем старые вебхуки и удаляем зависшие апдейты
    logging.info("Очистка старых вебхуков и зависших запросов...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Пауза перед стартом поллинга для избежания конфликтов
    await asyncio.sleep(2)
    
    # Запускаем поллинг сообщений
    logging.info("Запуск поллинга сообщений бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
