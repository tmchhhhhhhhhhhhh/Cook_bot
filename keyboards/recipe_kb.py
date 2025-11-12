from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_recipe_action_keyboard():
    """Клавиатура действий с рецептом"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Готовить!", callback_data="recipe_accept")],
        [InlineKeyboardButton(text="🔄 Другой вариант", callback_data="recipe_regenerate")]
    ])
    return keyboard


