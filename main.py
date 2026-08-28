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
        return [f"❌ Ошибка: {str(e)}"]# ===== КОМАНДЫ =====
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Привет! Я бот-парсер Avito.\n"
        "Введи название товара, чтобы найти объявления.\n"
        "Команды:\n"
        "/stats <товар> — статистика цен\n"
        "/start — это сообщение"
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

# ===== ФУНКЦИЯ ДЛЯ СБОРА ЦЕН =====
def get_prices_and_links(query):
    """
    Парсит Avito и возвращает список словарей:
    [{'title': ..., 'price': int, 'link': ...}, ...]
    """
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Referer': 'https://www.avito.ru/',
    }

    url = f"https://www.avito.ru/moskva?q={query}"
    session = requests.Session()
    session.headers.update(headers)

    try:
        # Добавляем задержку
        time.sleep(random.uniform(1.0, 2.5))
        response = session.get(url, timeout=15)

        if response.status_code != 200:
            return None  # ошибка

        if 'captcha' in response.text.lower():
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', {'data-marker': 'item'}) or soup.find_all('div', class_='iva-item-content-rejJg') or soup.find_all('article')

        results = []
        for item in items[:20]:  # берём до 20 для статистики
            # Заголовок
            title_tag = item.find('h3') or item.find('a', {'data-marker': 'item-title'})
            title = title_tag.text.strip() if title_tag else "Без названия"

            # Цена
            price_tag = item.find('span', {'itemprop': 'price'}) or item.find('span', class_='price-text-') or item.find('span', {'data-marker': 'item-price'})
            price_text = price_tag.text.strip() if price_tag else "0"
            # Очищаем от пробелов и символов валют
            price_cleaned = ''.join(filter(str.isdigit, price_text))
            price = int(price_cleaned) if price_cleaned else 0

            if price == 0:
                continue  # пропускаем без цены

            # Ссылка
            link_tag = item.find('a', {'data-marker': 'item-title'})
            link = f"https://www.avito.ru{link_tag['href']}" if link_tag and link_tag.get('href') else None

            results.append({
                'title': title,
                'price': price,
                'link': link
            })

        return results if results else None

    except Exception:
        return None

# ===== КОМАНДА /stats =====
@dp.message(Command("stats"))
async def stats_command(message: Message):
    # Разбираем запрос: /stats шорты
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❗ Укажите товар: `/stats шорты`")
        return

    query = args[1].strip()
    await message.answer(f"⏳ Собираю статистику для «{query}»...")

    data = get_prices_and_links(query)
    if not data:
        await message.answer("❌ Не удалось получить данные. Возможно, Avito блокирует запрос или товары не найдены.")
        return

    prices = [item['price'] for item in data]
    count = len(prices)
    if count == 0:
        await message.answer("❌ Нет объявлений с ценой.")
        return

    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / count

    # Формируем ответ
    answer = (
        f"📊 Статистика по запросу «{query}»:\n"
        f"📦 Найдено объявлений: {count}\n"
        f"🔻 Минимальная цена: {min_price:,} ₽\n"
        f"🔺 Максимальная цена: {max_price:,} ₽\n"
        f"📈 Средняя цена: {round(avg_price):,} ₽\n"
    )

    # Дополнительные рекомендации (если цена ниже среднего)
    if avg_price > 0:
        answer += f"\n💡 Рекомендуемая цена для перепродажи: ≤ {round(avg_price * 0.7):,} ₽ (скидка 30% от средней)"

    await message.answer(answer)

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
