import asyncio
from playwright.async_api import async_playwright
import random

async def search_kaspi(query):
    # Убираем лишнее, если AI все же выдал
    clean_query = query.replace('"', '').replace("'", "").strip()
    print(f"🔴 (Kaspi) Ищу: {clean_query}")

    async with async_playwright() as p:
        # ЗАПУСК С АРГУМЕНТАМИ ДЛЯ СКРЫТИЯ БОТА
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"] # Скрывает, что это автотест
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            # Добавляем заголовки как у реального браузера
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        # Магия для обхода детектов
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()

        try:
            url = f"https://kaspi.kz/shop/search/?text={clean_query}"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000) # Уменьшил таймаут

            # Ждем любой контент - или товары, или ошибку
            try:
                # Ждем либо карточки, либо капчу (если бы мы ее обрабатывали)
                await page.wait_for_selector(".item-card", timeout=10000)
            except:
                print("🔴 Kaspi: Карточки не найдены (возможно капча или пустой поиск)")
                # Можно сделать скриншот для отладки, но мы не увидим его на сервере
                return []

            cards = await page.locator(".item-card").all()
            results = []
            
            forbidden_words = ['чехол', 'стекло', 'пленка', 'аксессуар'] # Фильтр мусора

            for card in cards[:5]: # Берем только топ-5
                try:
                    name = await card.locator(".item-card__name-link").inner_text()
                    if any(w in name.lower() for w in forbidden_words): continue

                    price_text = await card.locator(".item-card__prices-price").first.inner_text()
                    price = int(''.join(filter(str.isdigit, price_text)))
                    
                    href = await card.locator(".item-card__name-link").get_attribute("href")
                    if href and not href.startswith("http"): href = f"https://kaspi.kz{href}"

                    img_el = card.locator("img").first
                    img_src = await img_el.get_attribute("src")

                    # Рейтинг
                    rating = "5.0"
                    reviews = "0"
                    try:
                        reviews_text = await card.locator(".item-card__rating a").inner_text()
                        reviews = ''.join(filter(str.isdigit, reviews_text))
                    except: pass

                    results.append({
                        "store": "Kaspi",
                        "name": name,
                        "price": price,
                        "rating": rating,
                        "reviews": reviews,
                        "currency": "₸",
                        "link": href,
                        "image": img_src
                    })
                except:
                    continue

            print(f"✅ Kaspi: Найдено {len(results)}")
            return results

        except Exception as e:
            print(f"❌ Ошибка Kaspi: {e}")
            return []
        finally:
            await browser.close()