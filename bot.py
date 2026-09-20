import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from google import genai
from google.genai import types

# --- Настройки ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ВАШ_ТОКЕН_БОТА")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "ВАШ_API_КЛЮЧ")
MODEL = "gemini-3.6-flash"  # бесплатная модель с поддержкой изображени...

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "Ты — помощник для решения школьных задач по фотографии. "
    "Внимательно прочитай условие на фото, реши задачу пошагово, "
    "объясни каждый шаг простым языком и дай итоговый ответ отдельной строкой в конце. "
    "Если на фото несколько задач — реши все по порядку."
    "ВАЖНО: пиши формулы обычным текстом без LaTeX, без знаков доллара $, без markdown-звёздочек ** и решёток ##. Используй простые символы: x, +, -, =, ^2 для степени."

)


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привет! Отправь мне фото школьной задачи (по математике, физике, "
        "химии и т.д.), и я помогу её решить с пошаговым объяснением."
    )


@dp.message(F.photo)
async def photo_handler(message: Message):
    processing_msg = await message.answer("Смотрю на задачу, думаю...")

    try:
        # Берём фото в максимальном качестве
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        image_bytes = file_bytes.read()

        caption = message.caption or "Реши задачу на фото."

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                caption,
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=2000,
            ),
        )

        answer_text = response.text

        # Telegram ограничивает сообщение 4096 символами — режем при необходимости
        for i in range(0, len(answer_text), 4000):
            await message.answer(answer_text[i : i + 4000])

    except Exception as e:
        logging.exception("Ошибка при обработке фото")
        await message.answer(
            f"Не получилось решить задачу. Попробуйте ещё раз или пришлите фото почётче.\n\nОшибка: {e}"
        )
    finally:
        await processing_msg.delete()


@dp.message(F.text)
async def text_handler(message: Message):
    await message.answer(
        "Пришлите, пожалуйста, фото задачи — я работаю с изображениями."
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
