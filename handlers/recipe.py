from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import html

from models.user import UserProfile, Recipe
from database import db
from services.ai_service import generate_recipe
from keyboards.recipe_kb import get_recipe_action_keyboard
from states.states import RecipeStates
from config import RECIPE_HISTORY_SIZE

router = Router()


@router.message(F.text, ~F.text.startswith('/'))
async def handle_recipe_request(message: Message, state: FSMContext, user_profile: UserProfile = None):
    """Обработка запроса на рецепт"""
    if not user_profile:
        await message.answer("Сначала зарегистрируйся! Напиши /start")
        return

    # Проверяем активную готовку
    session = await db.get_cooking_session(user_profile.user_id)
    if session:
        await message.answer(
            "⚠️ У тебя уже есть активная готовка!\n"
            "Заверши текущую готовку или отмени её командой /cancel_cooking"
        )
        return

    await message.answer("🔍 Ищу подходящий рецепт...")
    await state.update_data(request=message.text)

    # История рецептов (чтобы не повторять)
    recent_recipes = await db.get_recent_recipe_names(user_profile.user_id, RECIPE_HISTORY_SIZE)

    # Генерация рецепта
    recipe = await generate_recipe(
        user_profile=user_profile,
        dish_request=message.text,
        exclude_recipes=recent_recipes
    )

    if not recipe:
        await message.answer("😔 Не удалось сгенерировать рецепт. Попробуй переформулировать запрос.")
        await state.clear()
        return

    # Сохраняем рецепт во временное состояние
    await state.update_data(recipe=recipe)

    # Форматируем текст
    ingredients_text = '\n'.join([
        f"• {html.escape(ing['name'])} - {html.escape(ing['amount'])}"
        for ing in recipe.ingredients
    ])

    recipe_text = (
        f"🍽 <b>{html.escape(recipe.name)}</b>\n\n"
        f"<i>{html.escape(recipe.description)}</i>\n\n"
        f"⏱ Время: {recipe.cooking_time} мин\n"
        f"📊 КБЖУ на порцию:\n"
        f"  • Калории: {recipe.calories} ккал\n"
        f"  • Белки: {recipe.protein} г\n"
        f"  • Жиры: {recipe.fats} г\n"
        f"  • Углеводы: {recipe.carbs} г\n\n"
        f"🛒 <b>Ингредиенты:</b>\n{ingredients_text}"
    )

    await message.answer(
        recipe_text,
        parse_mode="HTML",
        reply_markup=get_recipe_action_keyboard()
    )


@router.callback_query(F.data == "recipe_accept")
async def accept_recipe(callback: CallbackQuery, state: FSMContext, user_profile: UserProfile):
    """Принятие рецепта и начало готовки"""
    data = await state.get_data()
    recipe: Recipe = data.get('recipe')

    if not recipe:
        await callback.answer("Рецепт не найден", show_alert=True)
        return

    # Сохраняем рецепт в БД и добавляем в историю
    recipe_id = await db.save_recipe(recipe)
    recipe.recipe_id = recipe_id
    await db.add_recipe_to_history(user_profile.user_id, recipe.name)

    # Начинаем готовку
    from handlers.cooking import start_cooking_session
    await start_cooking_session(callback.message, recipe, user_profile.user_id)

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "recipe_regenerate")
async def regenerate_recipe(callback: CallbackQuery, state: FSMContext, user_profile: UserProfile):
    """Регенерация нового рецепта"""
    data = await state.get_data()

    old_recipe: Recipe = data.get('recipe')
    dish_request: str = data.get('request')

    if not dish_request:
        await callback.message.answer("❌ Не найден исходный запрос для генерации.")
        await state.clear()
        await callback.answer()
        return

    await callback.message.answer("🔁 Генерирую новый рецепт...")

    # Добавляем старый рецепт в исключения
    recent_recipes = await db.get_recent_recipe_names(user_profile.user_id, RECIPE_HISTORY_SIZE)
    if old_recipe and old_recipe.name not in recent_recipes:
        recent_recipes.append(old_recipe.name)

    new_recipe = await generate_recipe(
        user_profile=user_profile,
        dish_request=dish_request,
        exclude_recipes=recent_recipes
    )

    if not new_recipe:
        await callback.message.answer("😔 Не удалось сгенерировать новый рецепт. Попробуй изменить запрос.")
        await state.clear()
        await callback.answer()
        return

    await state.update_data(recipe=new_recipe)

    ingredients_text = '\n'.join([
        f"• {html.escape(ing['name'])} - {html.escape(ing['amount'])}"
        for ing in new_recipe.ingredients
    ])

    recipe_text = (
        f"🍽 <b>{html.escape(new_recipe.name)}</b>\n\n"
        f"<i>{html.escape(new_recipe.description)}</i>\n\n"
        f"⏱ Время: {new_recipe.cooking_time} мин\n"
        f"📊 КБЖУ на порцию:\n"
        f"  • Калории: {new_recipe.calories} ккал\n"
        f"  • Белки: {new_recipe.protein} г\n"
        f"  • Жиры: {new_recipe.fats} г\n"
        f"  • Углеводы: {new_recipe.carbs} г\n\n"
        f"🛒 <b>Ингредиенты:</b>\n{ingredients_text}"
    )

    await callback.message.answer(
        recipe_text,
        parse_mode="HTML",
        reply_markup=get_recipe_action_keyboard()
    )
    await callback.answer()
