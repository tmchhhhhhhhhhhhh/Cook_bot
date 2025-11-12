from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class UserProfile:
    """Профиль пользователя"""
    user_id: int
    name: str
    goal: str  # 'weight_loss', 'muscle_gain', 'high_protein'
    dietary_restrictions: List[str]  # ['vegan', 'muslim', 'fasting', etc.]
    has_oven: bool
    has_microwave: bool
    has_stove: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class Recipe:
    """Рецепт блюда"""
    recipe_id: Optional[int]
    user_id: int
    name: str
    description: str
    calories: int
    protein: int
    fats: int
    carbs: int
    cooking_time: int  # в минутах
    ingredients: List[dict]  # [{"name": "...", "amount": "..."}]
    steps: List[dict]  # [{"step": 1, "description": "...", "duration": 5}]
    image_url: Optional[str]
    created_at: datetime
    is_favorite: bool = False


@dataclass
class CookingSession:
    """Активная сессия готовки"""
    session_id: Optional[int]
    user_id: int
    recipe_id: int
    current_step: int
    timer_end: Optional[datetime]  # Когда закончится текущий шаг
    is_paused: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class RecipeHistory:
    """История сгенерированных рецептов (для избежания повторов)"""
    user_id: int
    recipe_name: str
    created_at: datetime