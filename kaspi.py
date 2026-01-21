import asyncio
from playwright.async_api import async_playwright
import random

async def search_kaspi(query):
    # Очистка от кавычек
    clean_query = query.replace('"', '').replace("'", "").strip()
    print(f"🔴 (Kaspi) Ищу: {clean_query}")

    async with async_playwright() as p:
        # ЗАПУСКАЕМ БРАУЗЕР С "АНТИ-БОТ" АРГУМЕНТАМИ
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled", # Самое важное: скрывает, что это скрипт
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu"
            ]
        )
        
        # ЭМУЛИРУЕМ ОБЫЧНОГО ПОЛЬЗОВАТЕЛЯ
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ru-RU",
            timezone_id="Asia/Almaty"
        )
        
        # Магия JS, чтобы скрыть Playwright
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()

        try:
            # Сначала идем на главную, чтобы получить Cookies
            try:
                await page.goto("https://kaspi.kz/shop/", timeout=30000)
                await asyncio.sleep(1) # Короткая пауза
            except:
                pass # Если главная не прогрузилась, не страшно, пробуем поиск

            # Теперь поиск
            url = f"https://kaspi.kz/shop/search/?text={clean_query}"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Ждем селектор чуть дольше
            try:
                await page.wait_for_selector(".item-card", timeout=20000)
            except:
                print("🔴 Kaspi: Пусто (возможно капча или блок)")
                return []

            cards = await page.locator(".item-card").all()
            results = []
            
            forbidden = ['чехол', 'стекло', 'пленка']

            for card in cards[:5]:
                try:
                    name = await card.locator(".item-card__name-link").inner_text()
                    if any(w in name.lower() for w in forbidden): continue

                    price_text = await card.locator(".item-card__prices-price").first.inner_text()
                    price = int(''.join(filter(str.isdigit, price_text)))
                    
                    href = await card.locator(".item-card__name-link").get_attribute("href")
                    if href and not href.startswith("http"): href = f"https://kaspi.kz{href}"

                    img_src = await card.locator("img").first.get_attribute("src")

                    results.append({
                        "store": "Kaspi",
                        "name": name,
                        "price": price,
                        "link": href,
                        "image": img_src,
                        "rating": "5.0",
                        "reviews": "0"
                    })
                except:
                    continue

            print(f"✅ Kaspi: Найдено {len(results)}")
            return results

        except Exception as e:
            print(f"Ошибка Kaspi: {e}")
            return []
        finally:
            await browser.close()