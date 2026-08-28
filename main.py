import asyncio
import sys
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command

# ===== ТВОЙ ТОКЕН =====
TOKEN = "8665553820:AAEemdcHHg9IJpHBtywMxBrHqdQmkqFPqLs"

# ===== НАСТРОЙКА ПРОКСИ (если нужен) =====
# Если не используешь прокси, просто закомментируй строку PROXY
PROXY = "180.148.25.78"  # Например: "http://user:pass@ip:port" или "http://ip:port"

# ===== СОЗДАНИЕ БОТА =====
# Если прокси указан, используем его, иначе без прокси
if PROXY:
    bot = Bot(token=TOKEN, proxy=PROXY)
else:
    bot = Bot(token=TOKEN)

dp = Dispatcher()

# ===== ФУНКЦИЯ ПАРСИНГА AVITO =====
def parse_avito(query):
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    url = f"https://www.avito.ru/moskva?q={query}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='iva-item-content-rejJg')
        results = []
        for item in items[:5]:
            price_tag = item.find('span', class_='price-text-')
            price = price_tag.text.strip() if price_tag else "Цена не указана"
            title_tag = item.find('h3', class_='title-root-')
            title = title_tag.text.strip() if title_tag else "Без названия"
            results.append(f"{title}\n💰 {price}\n---")
        return results if results else ["❌ Товары не найдены"]
    except Exception as e:
        return [f"❌ Ошибка: {str(e)}"]

# ===== КОМАНДЫ =====
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Привет! Я бот-парсер Avito.\n"
        "Введи название товара, например:\n"
        "🔹 iphone 13\n"
        "🔹 велосипед"
    )

@dp.message()
async def handle_message(message: Message):
    query = message.text.strip()
    await message.answer(f"⏳ Ищу «{query}»...")
    data = parse_avito(query)
    answer = "🔍 Результаты:\n\n" + "\n".join(data)
    await message.answer(answer[:4000])

# ===== ЗАПУСК С ПРАВИЛЬНЫМ ЦИКЛОМ =====
async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Для Windows иногда нужно установить другую политику цикла
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        # Пытаемся получить существующий цикл
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Если нет — создаём новый
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(main())