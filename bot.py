import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from urllib.parse import quote

API_TOKEN = "8779551329:AAGORWqEaSry-OHWowHcYvktQaiYfiei6wo"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


async def search_wikipedia(query: str):
    headers = {
        "User-Agent": "TelegramWikiBot/1.0 (https://t.me/your_bot)"
    }

    async with aiohttp.ClientSession() as session:
        # Используем opensearch — он надёжнее
        search_url = "https://ru.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": 1,
            "namespace": 0,
            "format": "json"
        }

        async with session.get(search_url, params=params, headers=headers) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

        if not data or len(data) < 2 or not data[1]:
            return None

        title = data[1][0]

        # Получаем краткое описание
        summary_url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
        async with session.get(summary_url, headers=headers) as resp:
            if resp.status != 200:
                return None
            summary = await resp.json()

    return {
        "title": summary.get("title", title),
        "extract": summary.get("extract", "Описание отсутствует."),
        "url": summary.get("content_urls", {}).get("desktop", {}).get("page", "")
    }


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот, который ищет ответы в русской Википедии.\n\n"
        "Просто напиши любой вопрос или тему."
    )


@dp.message(F.text)
async def wiki_handler(message: types.Message):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Слишком короткий запрос.")
        return

    wait_msg = await message.answer("Ищу в Википедии...")

    try:
        result = await search_wikipedia(query)

        if not result:
            await wait_msg.edit_text("Ничего не нашёл в русской Википедии по этому запросу.")
            return

        text = (
            f"<b>{result['title']}</b>\n\n"
            f"{result['extract']}\n\n"
            f"<a href='{result['url']}'>Читать полностью</a>"
        )

        await wait_msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=False)

    except Exception as e:
        await wait_msg.edit_text(f"Произошла ошибка: {e}")


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
