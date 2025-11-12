from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime, timedelta
import asyncio

from models.user import Recipe, CookingSession
from database import db
from keyboards.cooking_kb import get_cooking_keyboard, get_completion_keyboard

router = Router()


async def start_cooking_session(message: Message, recipe: Recipe, user_id: int):
    """Начало сессии готовки"""
    # Создаем сессию
    session = CookingSession(
        session_id=None,
        user_id=user_id,
        recipe_id=recipe.recipe_id,
        current_step=0,
        timer_end=None,
        is_paused=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    await db.save_cooking_session(session)
    
    # Отправляем первый шаг
    await send_cooking_step(message, recipe, session)


async def send_cooking_step(message: Message, recipe: Recipe, session: CookingSession):
    """Отправка текущего шага готовки и установка таймера"""
    step_data = recipe.steps[session.current_step]
    total_steps = len(recipe.steps)

    duration = step_data.get('duration', 1)  # минимум 1 минута
    step_text = (
        f"👨‍🍳 *Шаг {session.current_step + 1} из {total_steps}*\n\n"
        f"{step_data['description']}\n\n"
        f"⏱ Время: {duration} мин"
    )

    # Устанавливаем таймер и сохраняем в БД до отправки сообщения
    session.timer_end = datetime.now() + timedelta(minutes=duration)
    session.updated_at = datetime.now()
    await db.update_cooking_session(session)

    print(f"⏰ Таймер установлен для user {session.user_id}: {session.timer_end}")

    await message.answer(
        step_text,
        parse_mode="Markdown",
        reply_markup=get_cooking_keyboard(is_paused=session.is_paused)
    )

    # Запускаем фоновую задачу для проверки таймера
    asyncio.create_task(check_timer(message.bot, session.user_id, session.session_id))


async def check_timer(bot, user_id: int, session_id: int):
    """Фоновая проверка таймера и переход к следующему шагу"""
    while True:
        await asyncio.sleep(10)  # Проверка каждые 10 секунд

        session = await db.get_cooking_session(user_id)

        if not session or session.session_id != session_id:
            # Сессия завершена или изменена
            break

        if session.is_paused:
            continue

        if not session.timer_end:
            # Таймер ещё не установлен, ждём
            await asyncio.sleep(1)
            continue

        if datetime.now() >= session.timer_end:
            # Таймер истёк — следующий шаг или завершение
            recipe = await db.get_recipe(session.recipe_id)

            if session.current_step < len(recipe.steps) - 1:
                session.current_step += 1
                session.updated_at = datetime.now()
                await db.update_cooking_session(session)

                try:
                    temp_message = type('Message', (), {
                        'bot': bot,
                        'chat': type('Chat', (), {'id': user_id})()
                    })()

                    await bot.send_message(
                        user_id,
                        f"✅ Шаг {session.current_step} завершен!"
                    )

                    await send_cooking_step(temp_message, recipe, session)
                except Exception as e:
                    print(f"Ошибка отправки сообщения: {e}")

            else:
                # Все шаги пройдены — готовка завершена
                await db.delete_cooking_session(user_id)
                try:
                    await bot.send_message(
                        user_id,
                        f"🎉 *Поздравляю!*\n\n"
                        f"Блюдо '{recipe.name}' готово! Приятного аппетита! 😋",
                        parse_mode="Markdown",
                        reply_markup=get_completion_keyboard(recipe.recipe_id)
                    )
                except Exception as e:
                    print(f"Ошибка отправки финального сообщения: {e}")

            break



@router.callback_query(F.data == "cooking_next")
async def next_step(callback: CallbackQuery):
    """Переход к следующему шагу"""
    session = await db.get_cooking_session(callback.from_user.id)
    
    if not session:
        await callback.answer("Активная готовка не найдена", show_alert=True)
        return
    
    recipe = await db.get_recipe(session.recipe_id)
    
    if session.current_step < len(recipe.steps) - 1:
        session.current_step += 1
        session.updated_at = datetime.now()
        await db.update_cooking_session(session)
        
        await callback.message.answer("➡️ Переходим к следующему шагу")
        await send_cooking_step(callback.message, recipe, session)
    else:
        # Завершаем готовку
        await db.delete_cooking_session(callback.from_user.id)
        await callback.message.answer(
            f"🎉 *Поздравляю!*\n\n"
            f"Блюдо '{recipe.name}' готово! Приятного аппетита! 😋",
            parse_mode="Markdown",
            reply_markup=get_completion_keyboard(recipe.recipe_id)
        )
    
    await callback.answer()


@router.callback_query(F.data == "cooking_pause")
async def pause_cooking(callback: CallbackQuery):
    """Пауза готовки"""
    session = await db.get_cooking_session(callback.from_user.id)
    
    if not session:
        await callback.answer("Активная готовка не найдена", show_alert=True)
        return
    
    session.is_paused = True
    session.updated_at = datetime.now()
    await db.update_cooking_session(session)
    
    await callback.answer("⏸ Готовка на паузе")
    await callback.message.answer(
        "⏸ *Готовка на паузе*\n\n"
        "Нажми 'Продолжить' когда будешь готов продолжить.",
        parse_mode="Markdown",
        reply_markup=get_cooking_keyboard(is_paused=True)
    )


@router.callback_query(F.data == "cooking_resume")
async def resume_cooking(callback: CallbackQuery):
    """Продолжение готовки"""
    session = await db.get_cooking_session(callback.from_user.id)
    
    if not session:
        await callback.answer("Активная готовка не найдена", show_alert=True)
        return
    
    session.is_paused = False
    session.updated_at = datetime.now()
    await db.update_cooking_session(session)
    
    await callback.answer("▶️ Готовка возобновлена")
    await callback.message.answer("▶️ Готовка возобновлена!")


@router.callback_query(F.data.in_({"timer_add", "timer_sub"}))
async def modify_timer(callback: CallbackQuery):
    """Изменение таймера (добавить/убавить минуту)"""
    session = await db.get_cooking_session(callback.from_user.id)

    # Проверка на активную готовку
    if not session:
        await callback.answer("❌ Активная готовка не найдена", show_alert=True)
        return

    # Проверка, активен ли таймер
    if not session.timer_end:
        await callback.answer("⏱ Подожди, таймер ещё запускается...", show_alert=True)
        return

    # Защита от паузы
    if session.is_paused:
        await callback.answer("⏸ Нельзя менять время на паузе", show_alert=True)
        return

    # Изменяем таймер
    if callback.data == "timer_add":
        session.timer_end += timedelta(minutes=1)
        text = "⏱ +1 минута добавлена"
    else:
        session.timer_end -= timedelta(minutes=1)
        text = "⏱ -1 минута убрана"

    # Сохраняем изменения
    session.updated_at = datetime.now()
    await db.update_cooking_session(session)

    await callback.answer(text)



@router.callback_query(F.data == "cooking_restart")
async def restart_cooking(callback: CallbackQuery):
    """Начать готовку заново"""
    session = await db.get_cooking_session(callback.from_user.id)
    
    if not session:
        await callback.answer("Активная готовка не найдена", show_alert=True)
        return
    
    recipe = await db.get_recipe(session.recipe_id)
    
    # Сбрасываем сессию
    session.current_step = 0
    session.is_paused = False
    session.updated_at = datetime.now()
    await db.update_cooking_session(session)
    
    await callback.message.answer("🔄 Начинаем заново!")
    await send_cooking_step(callback.message, recipe, session)
    await callback.answer()


@router.callback_query(F.data == "cooking_cancel")
@router.message(Command("cancel_cooking"))
async def cancel_cooking(event):
    """Отмена готовки"""
    user_id = event.from_user.id
    
    await db.delete_cooking_session(user_id)
    
    message = event.message if hasattr(event, 'message') else event
    await message.answer("❌ Готовка отменена")
    
    if hasattr(event, 'answer'):
        await event.answer()


@router.callback_query(F.data.startswith("complete_fav_"))
async def add_to_favorites(callback: CallbackQuery):
    """Добавление в избранное после завершения"""
    recipe_id = int(callback.data.split("_")[2])
    
    await db.toggle_favorite(recipe_id)
    
    await callback.answer("⭐️ Добавлено в избранное!")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("complete_done_"))
async def complete_done(callback: CallbackQuery):
    """Завершение без добавления в избранное"""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Приятного аппетита! 😋")