from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from models.user import UserProfile
from database import db
from keyboards.favorites_kb import get_favorites_keyboard, get_favorite_detail_keyboard

router = Router()


@router.message(Command("favorites"))
async def cmd_favorites(message: Message, user_profile: UserProfile = None):
    """Команда /favorites - показать избранные рецепты"""
    if not user_profile:
        await message.answer("Сначала зарегистрируйся! Напиши /start")
        return
    
    favorites = await db.get_favorites(user_profile.user_id)
    
    if not favorites:
        await message.answer(
            "📂 Избранное пусто\n\n"
            "Готовь рецепты и добавляй понравившиеся в избранное!"
        )
        return
    
    await message.answer(
        f"⭐️ *Твои избранные рецепты* ({len(favorites)}):\n\n"
        "Выбери рецепт:",
        parse_mode="Markdown",
        reply_markup=get_favorites_keyboard(favorites)
    )


@router.callback_query(F.data.startswith("fav_view_"))
async def view_favorite(callback: CallbackQuery):
    """Просмотр избранного рецепта"""
    recipe_id = int(callback.data.split("_")[2])
    recipe = await db.get_recipe(recipe_id)
    
    if not recipe:
        await callback.answer("Рецепт не найден", show_alert=True)
        return
    
    # Форматируем ингредиенты
    ingredients_text = '\n'.join([
        f"• {ing['name']} - {ing['amount']}"
        for ing in recipe.ingredients
    ])
    
    # Форматируем шаги
    steps_text = '\n\n'.join([
        f"*Шаг {step['step']}* ({step['duration']} мин):\n{step['description']}"
        for step in recipe.steps
    ])
    
    recipe_text = (
        f"🍽 *{recipe.name}*\n\n"
        f"_{recipe.description}_\n\n"
        f"⏱ Время: {recipe.cooking_time} мин\n"
        f"📊 КБЖУ на порцию:\n"
        f"  • Калории: {recipe.calories} ккал\n"
        f"  • Белки: {recipe.protein}г\n"
        f"  • Жиры: {recipe.fats}г\n"
        f"  • Углеводы: {recipe.carbs}г\n\n"
        f"🛒 *Ингредиенты:*\n{ingredients_text}\n\n"
        f"👨‍🍳 *Приготовление:*\n{steps_text}"
    )
    
    await callback.message.answer(
        recipe_text,
        parse_mode="Markdown",
        reply_markup=get_favorite_detail_keyboard(recipe_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fav_cook_"))
async def cook_favorite(callback: CallbackQuery, user_profile: UserProfile):
    """Начать готовку избранного рецепта"""
    recipe_id = int(callback.data.split("_")[2])
    
    # Проверяем активную готовку
    session = await db.get_cooking_session(user_profile.user_id)
    if session:
        await callback.answer(
            "⚠️ У тебя уже есть активная готовка! Завершите её или отмените.",
            show_alert=True
        )
        return
    
    recipe = await db.get_recipe(recipe_id)
    
    if not recipe:
        await callback.answer("Рецепт не найден", show_alert=True)
        return
    
    # Начинаем готовку
    from handlers.cooking import start_cooking_session
    await start_cooking_session(callback.message, recipe, user_profile.user_id)
    await callback.answer("👨‍🍳 Начинаем готовить!")


@router.callback_query(F.data.startswith("fav_remove_"))
async def remove_favorite(callback: CallbackQuery):
    """Удалить рецепт из избранного"""
    recipe_id = int(callback.data.split("_")[2])
    
    await db.delete_favorite(recipe_id)
    
    await callback.message.edit_text("🗑 Рецепт удален из избранного")
    await callback.answer()