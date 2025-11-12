# keyboards/registration_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def get_goal_keyboard():
    """Клавиатура выбора цели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏃 Похудение", callback_data="goal_weight_loss")],
        [InlineKeyboardButton(text="💪 Набор массы", callback_data="goal_muscle_gain")],
        [InlineKeyboardButton(text="🥩 Высокие белки", callback_data="goal_high_protein")]
    ])
    return keyboard


def get_restrictions_keyboard(selected: List[str] = None):
    """Клавиатура пищевых ограничений"""
    selected = selected or []
    
    restrictions = [
        ("Веган", "vegan"),
        ("Вегетарианец", "vegetarian"),
        ("Мусульманин (халяль)", "muslim"),
        ("Пост", "fasting"),
        ("Без глютена", "gluten_free"),
        ("Без лактозы", "lactose_free"),
    ]
    
    buttons = []
    for name, value in restrictions:
        check = "✅ " if value in selected else ""
        buttons.append([InlineKeyboardButton(
            text=f"{check}{name}",
            callback_data=f"restriction_{value}"
        )])
    
    buttons.append([InlineKeyboardButton(text="✔️ Готово", callback_data="restrictions_done")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_equipment_keyboard(has_oven=False, has_microwave=False, has_stove=False):
    """Клавиатура выбора оборудования"""
    oven_check = "✅ " if has_oven else ""
    microwave_check = "✅ " if has_microwave else ""
    stove_check = "✅ " if has_stove else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{oven_check}Духовка", callback_data="equip_oven")],
        [InlineKeyboardButton(text=f"{microwave_check}Микроволновка", callback_data="equip_microwave")],
        [InlineKeyboardButton(text=f"{stove_check}Плита", callback_data="equip_stove")],
        [InlineKeyboardButton(text="✔️ Готово", callback_data="equipment_done")]
    ])
    return keyboard


def get_skip_keyboard():
    """Клавиатура пропуска"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")]
    ])


