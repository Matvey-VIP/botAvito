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
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random

def parse_avito(query):
    # Создаём сессию для сохранения кук
    session = requests.Session()
    
    # Формируем максимально реалистичные заголовки
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.avito.ru/',
    }
    
    # Обновляем заголовки сессии
    session.headers.update(headers)

    url = f"https://www.avito.ru/moskva?q={query}"

    try:
        # Имитация поведения человека: задержка
        time.sleep(random.uniform(1.5, 3.0))
        
        # Первый запрос — получаем страницу
        response = session.get(url, timeout=15)
        
        # Если 403 — пробуем через прокси (если они есть)
        if response.status_code == 403:
            # Можно попробовать использовать бесплатный прокси
            # (пример, но лучше иметь свой надёжный)
            proxy_list = [
                # Здесь можно вставить свои прокси, либо оставить пустым
                # 'http://123.45.67.89:8080',
            ]
            for proxy in proxy_list:
                try:
                    proxies = {'http': proxy, 'https': proxy}
                    response = session.get(url, proxies=proxies, timeout=15)
                    if response.status_code == 200:
                        break
                except:
                    continue
        
        # Проверяем статус
        if response.status_code != 200:
            return [f"❌ Ошибка доступа к Avito: статус {response.status_code}. Попробуйте позже или измените запрос."]

        # Проверка на капчу
        if 'captcha' in response.text.lower():
            return ["⚠️ Avito запросил капчу. Попробуйте позже или используйте прокси."]

        # Парсинг
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем карточки товаров (разные варианты)
        items = soup.find_all('div', {'data-marker': 'item'})
        if not items:
            items = soup.find_all('div', class_='iva-item-content-rejJg')
        if not items:
            items = soup.find_all('article')

        if not items:
            return ["❌ Товары не найдены. Возможно, Avito изменил структуру страницы."]

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

        return results if results else ["❌ Ничего не найдено. Попробуйте другое ключевое слово."]

    except requests.exceptions.RequestException as e:
        return [f"❌ Ошибка сети: {str(e)}"]
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
