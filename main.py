import sys
import asyncio
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from vision import recognize_product
from wb import search_wb
from kaspi import search_kaspi
import shutil
import os

# Фикс для Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://searcherwk.screcai.site", # Твой сайт на Vercel/ScrecAI
        "http://localhost:3000",           # Для локальных тестов
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel

# Создаем схему данных для текста
class SearchRequest(BaseModel):
    query: str

@app.post("/search-text")
async def search_by_text(request: SearchRequest):
    # Извлекаем строку из JSON
    product_name = request.query
    print(f"🔎 Текстовый поиск инициирован: {product_name}")
    
    try:
        # Запускаем те же функции поиска в WB и Kaspi
        wb_task = search_wb(product_name)
        kaspi_task = search_kaspi(product_name)
        
        # Ждем оба результата параллельно
        results_list = await asyncio.gather(wb_task, kaspi_task)
        
        all_results = results_list[0] + results_list[1]
        
        # Сортировка по цене (как и в фото-поиске)
        all_results.sort(key=lambda x: x['price'])
        
        return {
            "query": product_name,
            "results": all_results
        }
    except Exception as e:
        print(f"❌ Ошибка текстового поиска: {e}")
        return {"query": product_name, "results": [], "error": str(e)}

@app.post("/scan")
async def scan_product(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 1. AI Распознавание
        product_name = recognize_product(temp_filename)
        print(f"AI увидел: {product_name}")
        
        # 2. ПАРАЛЛЕЛЬНЫЙ ПОИСК (Только WB и Kaspi)
        wb_task = search_wb(product_name)
        kaspi_task = search_kaspi(product_name)
        
        # Ждем выполнения обоих
        results_list = await asyncio.gather(wb_task, kaspi_task)
        
        wb_items = results_list[0]
        kaspi_items = results_list[1]
        
        # Объединяем
        all_results = wb_items + kaspi_items
        
        # Сортируем по цене (от дешевых к дорогим)
        all_results.sort(key=lambda x: x['price'])
        
        return {
            "query": product_name,
            "results": all_results
        }
        
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except:
                pass

if __name__ == "__main__":
    import uvicorn
    # reload=False для стабильности
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)