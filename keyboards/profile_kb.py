from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_profile_menu_keyboard():
    """Клавиатура меню профиля"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить имя", callback_data="edit_name")],
        [InlineKeyboardButton(text="🎯 Изменить цель", callback_data="edit_goal")],
        [InlineKeyboardButton(text="🍽 Изменить ограничения", callback_data="edit_restrictions")],
        [InlineKeyboardButton(text="🔧 Изменить оборудование", callback_data="edit_equipment")]
    ])
    return keyboard

