import asyncio
from playwright.async_api import async_playwright

async def search_wb(query):
    clean_query = query.replace('"', '').replace("'", "").strip()
    print(f"🟣 (WB) Ищу: {clean_query}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled", # СКРЫВАЕМ БОТА
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Скрываем свойство navigator.webdriver
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()

        try:
            url = f"https://www.wildberries.kz/catalog/0/search.aspx?search={clean_query}"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            try:
                await page.wait_for_selector(".product-card__link", timeout=20000)
            except:
                print("🟣 WB: Пусто (возможно капча)")
                return []

            cards = await page.locator(".product-card").all()
            results = []
            
            for card in cards[:6]:
                try:
                    name = await card.locator(".product-card__name").inner_text()
                    price_text = await card.locator(".price__lower-price").inner_text()
                    price = int(''.join(filter(str.isdigit, price_text)))
                    
                    href = await card.locator(".product-card__link").get_attribute("href")
                    link = href if href.startswith("http") else f"https://www.wildberries.kz{href}"
                    
                    img_src = await card.locator("img").first.get_attribute("src") or ""

                    results.append({
                        "store": "Wildberries",
                        "name": name,
                        "price": price,
                        "link": link,
                        "image": img_src,
                        "rating": "0",
                        "reviews": "0"
                    })
                except:
                    continue

            print(f"✅ WB: Найдено {len(results)}")
            return results

        except Exception as e:
            print(f"Ошибка WB: {e}")
            return []
        finally:
            await browser.close()