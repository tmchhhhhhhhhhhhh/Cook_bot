from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from database import db
print('hello')

class UserMiddleware(BaseMiddleware):
    """Middleware для загрузки профиля пользователя"""
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Загружаем профиль пользователя
        user_profile = await db.get_user(event.from_user.id)
        data['user_profile'] = user_profile
        
        return await handler(event, data)