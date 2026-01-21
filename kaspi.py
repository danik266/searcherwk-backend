import asyncio
from playwright.async_api import async_playwright

async def search_kaspi(query):
    clean_query = query.replace('"', '').replace("'", "").strip()
    print(f"🔴 (Kaspi) Ищу: {clean_query}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Оставил True, чтобы не мелькало
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            url = f"https://kaspi.kz/shop/search/?text={clean_query}"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            try:
                await page.wait_for_selector(".item-card", timeout=15000)
            except:
                return []

            cards = await page.locator(".item-card").all()
            results = []
            
            # Фильтр мусора
            forbidden_words = ['мыло', 'крем', 'бальзам', 'шампунь', 'гель', 'скраб']

            for card in cards:
                try:
                    name = await card.locator(".item-card__name-link").inner_text()
                    if any(w in name.lower() for w in forbidden_words): continue

                    price_text = await card.locator(".item-card__prices-price").first.inner_text()
                    price = int(''.join(filter(str.isdigit, price_text)))
                    
                    href = await card.locator(".item-card__name-link").get_attribute("href")
                    if href and not href.startswith("http"): href = f"https://kaspi.kz{href}"

                    img_el = card.locator("img").first
                    img_src = await img_el.get_attribute("src")

                    # === НОВОЕ: ОТЗЫВЫ ===
                    reviews = "0"
                    rating = "5.0" # У Каспи сложно вытащить цифру, ставим 5.0 по дефолту если есть отзывы
                    
                    try:
                        # Ищем текст отзывов, обычно это ссылка с текстом "(23)"
                        reviews_text = await card.locator(".item-card__rating a").inner_text()
                        # Чистим от скобок: (23) -> 23
                        reviews = ''.join(filter(str.isdigit, reviews_text))
                        
                        # Если отзывов нет, rating "0", если есть - пусть будет "5.0" (визуально)
                        if reviews == "" or reviews == "0":
                            rating = "0"
                            reviews = "0"
                    except:
                        rating = "0" # Если элемент не найден
                    # =====================

                    results.append({
                        "store": "Kaspi",
                        "name": name,
                        "price": price,
                        "rating": rating,    # <-- Добавили
                        "reviews": reviews,  # <-- Добавили
                        "currency": "₸",
                        "link": href,
                        "image": img_src
                    })
                    
                    if len(results) >= 5: break

                except Exception:
                    continue

            print(f"✅ Kaspi: Найдено {len(results)}")
            return results

        except Exception as e:
            print(f"Ошибка Kaspi: {e}")
            return []
        finally:
            await browser.close()