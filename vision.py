from google import genai
from google.genai import types
import os

# ТВОЙ КЛЮЧ
GOOGLE_API_KEY = "AIzaSyBuGiKGwlzE5fOdEh2OltudinqaEdvc5KQ" 

client = genai.Client(api_key=GOOGLE_API_KEY)

def recognize_product(image_path):
    print(f"👀 Смотрю на {image_path}...")
    
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # ОБНОВЛЕННЫЙ ПРОМПТ: ТРЕБУЕМ ЦВЕТ И ДЕТАЛИ
        prompt = """
        Analyze the image strictly for e-commerce search.
        Identify:
        1. The specific type of product (e.g., Hoodie, Sneakers, Gaming Mouse).
        2. The DOMINANT COLOR (Very important).
        3. Brand or distinctive features if visible.
        
        Output ONLY a search query in Russian (3-6 words).
        Format: [Color] [Gender/Type] [Brand/Model].
        Example: Синяя мужская толстовка Nike
        """

        # Используем Lite (или 1.5-flash если Lite лимитирован)
        response = client.models.generate_content(
            model='gemini-2.0-flash-lite-preview-02-05', 
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    ]
                )
            ]
        )
        
        return response.text.strip()
        
    except Exception as e:
        # Fallback (запасной вариант)
        try:
             response = client.models.generate_content(
                model='gemini-flash-latest', 
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                        ]
                    )
                ]
            )
             return response.text.strip()
        except Exception as e2:
             return f"Ошибка AI: {e2}"