from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cooking_keyboard(is_paused=False):
    """Клавиатура управления готовкой"""
    if is_paused:
        buttons = [
            [InlineKeyboardButton(text="▶️ Продолжить", callback_data="cooking_resume")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cooking_cancel")]
        ]
    else:
        buttons = [
            [
                InlineKeyboardButton(text="⏱ -1 мин", callback_data="timer_sub"),
                InlineKeyboardButton(text="⏱ +1 мин", callback_data="timer_add")
            ],
            [InlineKeyboardButton(text="➡️ След. шаг", callback_data="cooking_next")],
            [InlineKeyboardButton(text="⏸ Пауза", callback_data="cooking_pause")],
            [InlineKeyboardButton(text="🔄 Начать заново", callback_data="cooking_restart")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cooking_cancel")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_completion_keyboard(recipe_id: int):
    """Клавиатура после завершения готовки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ В избранное", callback_data=f"complete_fav_{recipe_id}")],
        [InlineKeyboardButton(text="✔️ Готово", callback_data=f"complete_done_{recipe_id}")]
    ])
    return keyboard


