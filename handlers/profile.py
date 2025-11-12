from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from models.user import UserProfile
from database import db
from keyboards.profile_kb import get_profile_menu_keyboard
from keyboards.registration_kb import (
    get_goal_keyboard,
    get_restrictions_keyboard,
    get_equipment_keyboard
)
from states.states import ProfileStates

router = Router()


@router.message(Command("profile"))
async def cmd_profile(message: Message, user_profile: UserProfile = None):
    """Команда /profile"""
    if not user_profile:
        await message.answer("Сначала нужно зарегистрироваться! Напиши /start")
        return
    
    restrictions_text = ', '.join(user_profile.dietary_restrictions) if user_profile.dietary_restrictions else 'нет'
    
    equipment_list = []
    if user_profile.has_oven:
        equipment_list.append('духовка')
    if user_profile.has_microwave:
        equipment_list.append('микроволновка')
    if user_profile.has_stove:
        equipment_list.append('плита')
    equipment_text = ', '.join(equipment_list) if equipment_list else 'нет'
    
    goal_names = {
        'weight_loss': 'Похудение',
        'muscle_gain': 'Набор массы',
        'high_protein': 'Высокие белки'
    }
    
    await message.answer(
        f"👤 Твой профиль:\n\n"
        f"Имя: {user_profile.name}\n"
        f"Цель: {goal_names.get(user_profile.goal, user_profile.goal)}\n"
        f"Ограничения: {restrictions_text}\n"
        f"Оборудование: {equipment_text}\n\n"
        f"Что хочешь изменить?",
        reply_markup=get_profile_menu_keyboard()
    )


@router.callback_query(F.data == "edit_name")
async def edit_name(callback: CallbackQuery, state: FSMContext):
    """Редактирование имени"""
    await callback.message.edit_text("Введи новое имя:")
    await state.set_state(ProfileStates.edit_name)
    await callback.answer()


@router.message(ProfileStates.edit_name)
async def process_edit_name(message: Message, state: FSMContext, user_profile: UserProfile):
    """Обработка нового имени"""
    user_profile.name = message.text
    user_profile.updated_at = datetime.now()
    await db.save_user(user_profile)
    
    await message.answer(
        f"✅ Имя обновлено: {message.text}\n\n"
        "Используй /profile чтобы продолжить редактирование"
    )
    await state.clear()


@router.callback_query(F.data == "edit_goal")
async def edit_goal(callback: CallbackQuery, state: FSMContext):
    """Редактирование цели"""
    await callback.message.edit_text(
        "Выбери новую цель:",
        reply_markup=get_goal_keyboard()
    )
    await state.set_state(ProfileStates.edit_goal)
    await callback.answer()


@router.callback_query(ProfileStates.edit_goal, F.data.startswith("goal_"))
async def process_edit_goal(callback: CallbackQuery, state: FSMContext, user_profile: UserProfile):
    """Обработка новой цели"""
    goal = callback.data.split("_")[1]
    user_profile.goal = goal
    user_profile.updated_at = datetime.now()
    await db.save_user(user_profile)
    
    goal_names = {
        'weight_loss': 'Похудение',
        'muscle_gain': 'Набор массы',
        'high_protein': 'Высокие белки'
    }
    
    await callback.message.edit_text(
        f"✅ Цель обновлена: {goal_names[goal]}\n\n"
        "Используй /profile чтобы продолжить редактирование"
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit_restrictions")
async def edit_restrictions(callback: CallbackQuery, state: FSMContext, user_profile: UserProfile):
    """Редактирование ограничений"""
    await callback.message.edit_text(
        "Выбери пищевые ограничения:",
        reply_markup=get_restrictions_keyboard(selected=user_profile.dietary_restrictions)
    )
    await state.set_state(ProfileStates.edit_restrictions)
    await callback.answer()


@router.callback_query(ProfileStates.edit_restrictions, F.data.startswith("restriction_"))
async def process_restriction_toggle_edit(callback: CallbackQuery, state: FSMContext, user_profile: UserProfile):
    """Переключение ограничения при редактировании"""
    restriction = callback.data.split("_", 1)[1]
    
    if restriction in user_profile.dietary_restrictions:
        user_profile.dietary_restrictions.remove(restriction)
    else:
        user_profile.dietary_restrictions.append(restriction)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_restrictions_keyboard(selected=user_profile.dietary_restrictions)
    )
    await callback.answer()


@router.callback_query(ProfileStates.edit_restrictions, F.data == "restrictions_done")
async def process_restrictions_done_edit(callback: CallbackQuery, state: FSMContext, user_profile: UserProfile):
    """Сохранение ограничений"""
    user_profile.updated_at = datetime.now()
    await db.save_user(user_profile)
    
    restrictions_text = ', '.join(user_profile.dietary_restrictions) if user_profile.dietary_restrictions else 'нет'
    
    await callback.message.edit_text(
        f"✅ Ограничения обновлены: {restrictions_text}\n\n"
        "Используй /profile чтобы продолжить редактирование"
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit_equipment")
async def edit_equipment(callback: CallbackQuery, state: FSMContext, user_profile: UserProfile):
    """Редактирование оборудования"""
    await callback.message.edit_text(
        "Выбери доступное оборудование:",
        reply_markup=get_equipment_keyboard(
            has_oven=user_profile.has_oven,
            has_microwave=user_profile.has_microwave,
            has_stove=user_profile.has_stove
        )
    )
    await state.set_state(ProfileStates.edit_equipment)
    await callback.answer()


@router.callback_query(ProfileStates.edit_equipment, F.data.startswith("equip_"))
async def process_equipment_toggle_edit(callback: CallbackQuery, state: FSMContext, user_profile: UserProfile):
    """Переключение оборудования при редактировании"""
    equipment = callback.data.split("_")[1]
    
    if equipment == "oven":
        user_profile.has_oven = not user_profile.has_oven
    elif equipment == "microwave":
        user_profile.has_microwave = not user_profile.has_microwave
    elif equipment == "stove":
        user_profile.has_stove = not user_profile.has_stove
    
    await callback.message.edit_reply_markup(
        reply_markup=get_equipment_keyboard(
            has_oven=user_profile.has_oven,
            has_microwave=user_profile.has_microwave,
            has_stove=user_profile.has_stove
        )
    )
    await callback.answer()


@router.callback_query(ProfileStates.edit_equipment, F.data == "equipment_done")
async def process_equipment_done_edit(callback: CallbackQuery, state: FSMContext, user_profile: UserProfile):
    """Сохранение оборудования"""
    user_profile.updated_at = datetime.now()
    await db.save_user(user_profile)
    
    equipment_list = []
    if user_profile.has_oven:
        equipment_list.append('духовка')
    if user_profile.has_microwave:
        equipment_list.append('микроволновка')
    if user_profile.has_stove:
        equipment_list.append('плита')
    equipment_text = ', '.join(equipment_list) if equipment_list else 'нет'
    
    await callback.message.edit_text(
        f"✅ Оборудование обновлено: {equipment_text}\n\n"
        "Используй /profile чтобы продолжить редактирование"
    )
    await state.clear()
    await callback.answer()