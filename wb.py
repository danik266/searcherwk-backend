import asyncio
from playwright.async_api import async_playwright

async def search_wb(query):
    clean_query = query.replace('"', '').replace("'", "").strip()
    print(f"🟣 (Visual) Ищу на WB: {clean_query}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            search_url = f"https://www.wildberries.kz/catalog/0/search.aspx?search={clean_query}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)

            try:
                await page.wait_for_selector(".product-card__link", timeout=15000)
            except:
                return []

            cards = await page.locator(".product-card").all()
            results = []
            
            for card in cards[:6]:
                try:
                    name = await card.locator(".product-card__name").inner_text()
                    
                    price_text = await card.locator(".price__lower-price").inner_text()
                    price = int(''.join(filter(str.isdigit, price_text)))
                    
                    href = await card.locator(".product-card__link").get_attribute("href")
                    full_link = href if href.startswith("http") else f"https://www.wildberries.kz{href}"
                    
                    img_el = card.locator("img").first
                    img_src = await img_el.get_attribute("src")
                    if not img_src: img_src = ""

                    # === НОВОЕ: РЕЙТИНГ И ОТЗЫВЫ ===
                    rating = "0"
                    reviews = "0"
                    
                    # Пытаемся найти рейтинг (например "4.8")
                    try:
                        rating = await card.locator(".address-rate-mini").inner_text()
                    except:
                        pass # Нет рейтинга
                    
                    # Пытаемся найти кол-во отзывов (например "1 200 оценок")
                    try:
                        reviews_text = await card.locator(".product-card__count").inner_text()
                        # Оставляем только цифры
                        reviews = ''.join(filter(str.isdigit, reviews_text))
                    except:
                        pass
                    # ================================

                    results.append({
                        "store": "Wildberries",
                        "name": name,
                        "price": price,
                        "rating": rating,   # <-- Добавили
                        "reviews": reviews, # <-- Добавили
                        "currency": "₸",
                        "link": full_link,
                        "image": img_src
                    })
                except Exception:
                    continue

            print(f"✅ WB: Найдено {len(results)}")
            return results

        except Exception as e:
            print(f"Ошибка WB: {e}")
            return []
        finally:
            await browser.close()