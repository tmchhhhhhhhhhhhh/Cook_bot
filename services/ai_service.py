# services/ai_service.py
import requests
import json
from typing import Optional, List
from datetime import datetime
from models.user import UserProfile, Recipe
from config import AI_API_TOKEN, MODEL

API_URL = "https://router.huggingface.co/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {AI_API_TOKEN}",
    "Content-Type": "application/json"
}


def query(payload: dict) -> Optional[dict]:
    """Отправка запроса в Hugging Face API"""
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"[AI API ERROR] {response.status_code}: {response.text}")
            return None
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[AI API EXCEPTION] {e}")
        return None


def build_recipe_prompt(
    user_profile: UserProfile,
    dish_request: str,
    ingredients: Optional[List[str]] = None,
    exclude_recipes: Optional[List[str]] = None
) -> str:
    """Создание промпта для генерации рецепта"""
    goal_text = {
        "weight_loss": "похудение (низкокалорийное)",
        "muscle_gain": "набор мышечной массы (высокобелковое)",
        "none": "неважно"
    }.get(user_profile.goal, "")

    restrictions = ", ".join(user_profile.dietary_restrictions) if user_profile.dietary_restrictions else "нет"
    equipment = []
    if user_profile.has_oven:
        equipment.append("духовка")
    if user_profile.has_microwave:
        equipment.append("микроволновка")
    if user_profile.has_stove:
        equipment.append("плита")
    equipment_text = ", ".join(equipment) if equipment else "нет специального оборудования"
    ingredients_text = ", ".join(ingredients) if ingredients else "любые"

    exclude_text = ""
    if exclude_recipes:
        exclude_text = f"\n\nНЕ ПРЕДЛАГАЙ эти блюда (уже были): {', '.join(exclude_recipes)}"

    prompt = f"""Ты — профессиональный шеф-повар и диетолог. Создай детальный рецепт блюда.

ЗАПРОС: {dish_request}

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
- Имя: {user_profile.name}
- Цель: {goal_text}
- Пищевые ограничения: {restrictions}
- Доступное оборудование: {equipment_text}
- Предпочитаемые ингредиенты: {ingredients_text}{exclude_text}

ВАЖНО: Ответ должен быть строго в формате JSON, без markdown:
{{
    "name": "Название блюда",
    "description": "Краткое описание (1-2 предложения)",
    "calories": xxx,
    "protein": xxx,
    "fats": xxx,
    "carbs": xxx,
    "cooking_time": xxx,
    "ingredients": [
        {{"name": "Ингридиент1", "amount": "xxxг"}},
        {{"name": "Ингридиент2", "amount": "xxxг"}}
    ],
    "steps": [
        {{"step": 1, "description": "Нарезать курицу кубиками", "duration": 5}},
        {{"step": 2, "description": "Обжарить на сковороде до золотистой корочки", "duration": 10}},
        {{"step": 3, "description": "Отварить рис в подсоленной воде", "duration": 15}}
    ]
}}

Требования:
- КБЖУ должны соответствовать цели пользователя
- Учитывай пищевые ограничения
- Используй только доступное оборудование
- Время в минутах для каждого шага
- Общее время готовки = сумма всех шагов
- НЕ используй markdown, только чистый JSON
"""
    return prompt


def parse_recipe_response(response: dict, user_id: int) -> Optional[Recipe]:
    """Парсинг ответа AI в объект Recipe"""
    try:
        reply_text = response["choices"][0]["message"]["content"].strip()

        # Убираем блоки <think>...</think> и markdown ```
        if "<think>" in reply_text and "</think>" in reply_text:
            reply_text = reply_text.split("</think>")[-1].strip()

        if reply_text.startswith("```"):
            reply_text = reply_text.split("```")[-1].strip()
            if reply_text.startswith("json"):
                reply_text = reply_text[4:].strip()

        data = json.loads(reply_text)

        return Recipe(
            recipe_id=None,
            user_id=user_id,
            name=data["name"],
            description=data["description"],
            calories=int(data["calories"]),
            protein=int(data["protein"]),
            fats=int(data["fats"]),
            carbs=int(data["carbs"]),
            cooking_time=int(data["cooking_time"]),
            ingredients=data["ingredients"],
            steps=data["steps"],
            image_url=None,
            created_at=datetime.now(),
            is_favorite=False
        )

    except Exception as e:
        print(f"[AI PARSE ERROR] {e}")
        print(f"Ответ AI: {response}")
        return None

async def generate_recipe(
    user_profile: UserProfile,
    dish_request: str,
    ingredients: Optional[List[str]] = None,
    exclude_recipes: Optional[List[str]] = None
) -> Optional[Recipe]:
    """Генерация рецепта через Hugging Face API"""
    prompt = build_recipe_prompt(user_profile, dish_request, ingredients, exclude_recipes)
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = query(payload)
    if not response:
        print("[AI API ERROR] Пустой ответ")
        return None

    return parse_recipe_response(response, user_profile.user_id)

