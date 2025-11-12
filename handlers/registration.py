from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from states.states import RegistrationStates
from models.user import UserProfile
from database import db
from keyboards.registration_kb import (
    get_goal_keyboard,
    get_restrictions_keyboard,
    get_equipment_keyboard,
    get_skip_keyboard
)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user_profile: UserProfile = None):
    """Команда /start"""
    if user_profile:
        await message.answer(
            f"С возвращением, {user_profile.name}! 👋\n\n"
            "Напиши, что хочешь приготовить, и я помогу!\n\n"
            "Доступные команды:\n"
            "/profile - редактировать профиль\n"
            "/favorites - избранные рецепты"
        )
    else:
        await message.answer(
            "Привет! 👨‍🍳 Я помогу тебе готовить вкусные и полезные блюда!\n\n"
            "Давай начнем с твоего профиля. Как тебя зовут?"
        )
        await state.set_state(RegistrationStates.name)


@router.message(RegistrationStates.name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    await state.update_data(name=message.text)
    await message.answer(
        f"Приятно познакомиться, {message.text}! 😊\n\n"
        "Какая у тебя цель?",
        reply_markup=get_goal_keyboard()
    )
    await state.set_state(RegistrationStates.goal)


@router.callback_query(RegistrationStates.goal, F.data.startswith("goal_"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора цели"""
    goal = callback.data
    await state.update_data(goal=goal)
    
    goal_names = {
    'goal_weight_loss': 'Похудение',
    'goal_muscle_gain': 'Набор массы',
    'goal_high_protein': 'Высокие белки'
    }
    await callback.message.edit_text(
        f"Отлично! Цель: {goal_names[goal]} ✅\n\n"
        "Есть ли у тебя пищевые ограничения?",
        reply_markup=get_restrictions_keyboard()
    )
    await state.set_state(RegistrationStates.dietary_restrictions)
    await callback.answer()


@router.callback_query(RegistrationStates.dietary_restrictions, F.data == "restrictions_done")
async def process_restrictions_done(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора ограничений"""
    data = await state.get_data()
    restrictions = data.get('dietary_restrictions', [])
    
    if restrictions:
        restrictions_text = ', '.join(restrictions)
        text = f"Учту твои ограничения: {restrictions_text} ✅\n\n"
    else:
        text = "Ограничений нет ✅\n\n"
    
    await callback.message.edit_text(
        text + "Какое оборудование у тебя есть?",
        reply_markup=get_equipment_keyboard()
    )
    await state.set_state(RegistrationStates.equipment)
    await callback.answer()


@router.callback_query(RegistrationStates.dietary_restrictions, F.data.startswith("restriction_"))
async def process_restriction_toggle(callback: CallbackQuery, state: FSMContext):
    """Переключение ограничения"""
    restriction = callback.data.split("_", 1)[1]
    data = await state.get_data()
    restrictions = data.get('dietary_restrictions', [])
    
    if restriction in restrictions:
        restrictions.remove(restriction)
    else:
        restrictions.append(restriction)
    
    await state.update_data(dietary_restrictions=restrictions)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_restrictions_keyboard(selected=restrictions)
    )
    await callback.answer()


@router.callback_query(RegistrationStates.equipment, F.data.startswith("equip_"))
async def process_equipment_toggle(callback: CallbackQuery, state: FSMContext):
    """Переключение оборудования"""
    equipment = callback.data.split("_")[1]
    data = await state.get_data()
    
    # Обновляем состояние оборудования
    key = f"has_{equipment}"
    current_value = data.get(key, False)
    await state.update_data(**{key: not current_value})
    
    # Обновляем клавиатуру
    updated_data = await state.get_data()
    await callback.message.edit_reply_markup(
        reply_markup=get_equipment_keyboard(
            has_oven=updated_data.get('has_oven', False),
            has_microwave=updated_data.get('has_microwave', False),
            has_stove=updated_data.get('has_stove', False)
        )
    )
    await callback.answer()


@router.callback_query(RegistrationStates.equipment, F.data == "equipment_done")
async def process_equipment_done(callback: CallbackQuery, state: FSMContext):
    """Завершение регистрации"""
    data = await state.get_data()
    
    # Создаем профиль
    profile = UserProfile(
        user_id=callback.from_user.id,
        name=data['name'],
        goal=data['goal'],
        dietary_restrictions=data.get('dietary_restrictions', []),
        has_oven=data.get('has_oven', False),
        has_microwave=data.get('has_microwave', False),
        has_stove=data.get('has_stove', False),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    await db.save_user(profile)
    
    equipment_list = []
    if profile.has_oven:
        equipment_list.append('духовка')
    if profile.has_microwave:
        equipment_list.append('микроволновка')
    if profile.has_stove:
        equipment_list.append('плита')
    
    equipment_text = ', '.join(equipment_list) if equipment_list else 'нет'
    
    await callback.message.edit_text(
        f"🎉 Регистрация завершена!\n\n"
        f"👤 Имя: {profile.name}\n"
        f"🎯 Цель: {profile.goal}\n"
        f"🍽 Оборудование: {equipment_text}\n\n"
        f"Теперь просто напиши, что хочешь приготовить!\n"
        f"Например: 'Хочу курицу с овощами' или 'Омлет на завтрак'"
    )
    
    await state.clear()
    await callback.answer()