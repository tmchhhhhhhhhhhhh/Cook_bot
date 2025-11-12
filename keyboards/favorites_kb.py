from typing import List
from models.user import Recipe
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_favorites_keyboard(recipes: List[Recipe]):
    """Клавиатура списка избранного"""
    buttons = []
    
    for recipe in recipes:
        buttons.append([InlineKeyboardButton(
            text=f"🍽 {recipe.name} ({recipe.cooking_time} мин)",
            callback_data=f"fav_view_{recipe.recipe_id}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_favorite_detail_keyboard(recipe_id: int):
    """Клавиатура детального просмотра избранного"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍🍳 Начать готовить", callback_data=f"fav_cook_{recipe_id}")],
        [InlineKeyboardButton(text="🗑 Удалить из избранного", callback_data=f"fav_remove_{recipe_id}")]
    ])
    return keyboard