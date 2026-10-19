import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from urllib.parse import quote

API_TOKEN = "8779551329:AAGORWqEaSry-OHWowHcYvktQaiYfiei6wo"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


async def search_wildberries(query: str, limit: int = 8):
    url = "https://search.wb.ru/exactmatch/ru/common/v18/search"
    params = {
        "query": query,
        "resultset": "catalog",
        "limit": limit,
        "page": 1,
        "appType": 1,
        "curr": "rub",
        "dest": -1257786,
        "sort": "popular",
        "spp": 30
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"{resp.status}: {text[:200]}")
            data = await resp.json()
            
    products = data.get("data", {}).get("products", [])
    results = []
    
    for p in products[:limit]:
        price = p.get("salePriceU", p.get("priceU", 0)) // 100
        old_price = p.get("priceU", 0) // 100
        rating = p.get("reviewRating") or p.get("rating") or 0
        feedbacks = p.get("feedbacks", 0)
        name = p.get("name", "Без названия")
        brand = p.get("brand", "")
        article = p.get("id")
        
        link = f"https://www.wildberries.ru/catalog/{article}/detail.aspx"
        
        results.append({
            "name": f"{brand} {name}".strip(),
            "price": price,
            "old_price": old_price if old_price > price else None,
            "rating": rating,
            "feedbacks": feedbacks,
            "link": link
        })
    
    return results


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для поиска товаров на Wildberries и Ozon.\n\n"
        "Просто напиши название товара, например:\n"
        "<code>наушники sony</code>\n"
        "<code>кроссовки nike</code>\n"
        "<code>чехол iphone 15</code>",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text)
async def search_handler(message: types.Message):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Слишком короткий запрос.")
        return
    
    wait_msg = await message.answer("Ищу товары...")
    
    try:
        products = await search_wildberries(query)
        
        if not products:
            await wait_msg.edit_text("Ничего не нашёл на Wildberries.")
            return
        
        text = f"<b>Результаты поиска по запросу:</b> <code>{query}</code>\n\n"
        
        for i, p in enumerate(products, 1):
            price_str = f"{p['price']} ₽"
            if p['old_price']:
                price_str = f"<s>{p['old_price']} ₽</s> → <b>{p['price']} ₽</b>"
            
            text += (
                f"<b>{i}. {p['name']}</b>\n"
                f"Цена: {price_str}\n"
                f"Рейтинг: {p['rating']} ({p['feedbacks']} отзывов)\n"
                f"<a href='{p['link']}'>Открыть на WB</a>\n\n"
            )
        
        ozon_link = f"https://www.ozon.ru/search/?text={quote(query)}"
        text += f"——————\n🔍 <a href='{ozon_link}'>Искать этот же запрос на Ozon</a>"
        
        await wait_msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        
    except Exception as e:
        await wait_msg.edit_text(f"Произошла ошибка при поиске: {e}")


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
