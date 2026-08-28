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
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }

    url = f"https://www.avito.ru/moskva?q={query}"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # ---- ОТЛАДКА: сохраняем HTML в файл ----
        with open('debug_avito.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"DEBUG: HTML сохранён в debug_avito.html, длина {len(response.text)}")

        # Проверяем на капчу
        if 'captcha' in response.text.lower():
            return ["⚠️ Avito запросил капчу. Попробуйте позже."]

        soup = BeautifulSoup(response.text, 'html.parser')

        # Пробуем разные способы поиска товаров
        items = []
        # Способ 1: data-marker
        items = soup.find_all('div', {'data-marker': 'item'})
        if not items:
            # Способ 2: класс для карточки
            items = soup.find_all('div', class_='iva-item-content-rejJg')
        if not items:
            # Способ 3: поиск по статье (article) — часто используется
            items = soup.find_all('article')

        if not items:
            # Если ничего не нашли, выведем часть HTML для анализа
            snippet = response.text[:1000]
            return [f"❌ HTML не содержит карточек товаров.\nПервые 1000 символов:\n{snippet}"]

        results = []
        for item in items[:10]:
            # Заголовок
            title_tag = item.find('h3') or item.find('a', {'data-marker': 'item-title'})
            title = title_tag.text.strip() if title_tag else "Без названия"

            # Цена
            price_tag = item.find('span', {'itemprop': 'price'}) or item.find('span', class_='price-text-') or item.find('span', {'data-marker': 'item-price'})
            price = price_tag.text.strip() if price_tag else "Цена не указана"

            # Ссылка
            link_tag = item.find('a', {'data-marker': 'item-title'})
            if link_tag and link_tag.get('href'):
                link = f"https://www.avito.ru{link_tag['href']}"
            else:
                link = "Ссылка не найдена"

            results.append(f"{title}\n💰 {price}\n🔗 {link}\n---")

        return results if results else ["❌ Товары не найдены. Возможно, Avito вернул пустую страницу."]

    except Exception as e:
        return [f"❌ Ошибка: {str(e)}"]

===== КОМАНДЫ =====
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
