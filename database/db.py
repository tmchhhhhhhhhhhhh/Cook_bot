import aiosqlite
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from config import DB_PATH
from models.user import UserProfile, Recipe, CookingSession, RecipeHistory


async def init_db():
    """Инициализация базы данных"""
    Path("data").mkdir(exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                goal TEXT NOT NULL,
                dietary_restrictions TEXT,
                has_oven BOOLEAN,
                has_microwave BOOLEAN,
                has_stove BOOLEAN,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Таблица рецептов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                calories INTEGER,
                protein INTEGER,
                fats INTEGER,
                carbs INTEGER,
                cooking_time INTEGER,
                ingredients TEXT,
                steps TEXT,
                image_url TEXT,
                is_favorite BOOLEAN DEFAULT 0,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица активных сессий готовки
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cooking_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                recipe_id INTEGER,
                current_step INTEGER,
                timer_end TIMESTAMP,
                is_paused BOOLEAN DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id)
            )
        """)
        
        # История рецептов для избежания повторов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recipe_history (
                user_id INTEGER,
                recipe_name TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        await db.commit()


async def get_user(user_id: int) -> Optional[UserProfile]:
    """Получить профиль пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return UserProfile(
                    user_id=row[0],
                    name=row[1],
                    goal=row[2],
                    dietary_restrictions=json.loads(row[3]) if row[3] else [],
                    has_oven=bool(row[4]),
                    has_microwave=bool(row[5]),
                    has_stove=bool(row[6]),
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8])
                )
    return None


async def save_user(profile: UserProfile):
    """Сохранить профиль пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, name, goal, dietary_restrictions, has_oven, has_microwave, 
             has_stove, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.user_id,
            profile.name,
            profile.goal,
            json.dumps(profile.dietary_restrictions),
            profile.has_oven,
            profile.has_microwave,
            profile.has_stove,
            profile.created_at.isoformat(),
            profile.updated_at.isoformat()
        ))
        await db.commit()


async def save_recipe(recipe: Recipe) -> int:
    """Сохранить рецепт и вернуть его ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO recipes 
            (user_id, name, description, calories, protein, fats, carbs, 
             cooking_time, ingredients, steps, image_url, is_favorite, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe.user_id,
            recipe.name,
            recipe.description,
            recipe.calories,
            recipe.protein,
            recipe.fats,
            recipe.carbs,
            recipe.cooking_time,
            json.dumps(recipe.ingredients),
            json.dumps(recipe.steps),
            recipe.image_url,
            recipe.is_favorite,
            recipe.created_at.isoformat()
        ))
        await db.commit()
        return cursor.lastrowid


async def get_recipe(recipe_id: int) -> Optional[Recipe]:
    """Получить рецепт по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM recipes WHERE recipe_id = ?", (recipe_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Recipe(
                    recipe_id=row[0],
                    user_id=row[1],
                    name=row[2],
                    description=row[3],
                    calories=row[4],
                    protein=row[5],
                    fats=row[6],
                    carbs=row[7],
                    cooking_time=row[8],
                    ingredients=json.loads(row[9]),
                    steps=json.loads(row[10]),
                    image_url=row[11],
                    is_favorite=bool(row[12]),
                    created_at=datetime.fromisoformat(row[13])
                )
    return None


async def get_favorites(user_id: int) -> List[Recipe]:
    """Получить избранные рецепты пользователя"""
    recipes = []
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM recipes WHERE user_id = ? AND is_favorite = 1 ORDER BY created_at DESC",
            (user_id,)
        ) as cursor:
            async for row in cursor:
                recipes.append(Recipe(
                    recipe_id=row[0],
                    user_id=row[1],
                    name=row[2],
                    description=row[3],
                    calories=row[4],
                    protein=row[5],
                    fats=row[6],
                    carbs=row[7],
                    cooking_time=row[8],
                    ingredients=json.loads(row[9]),
                    steps=json.loads(row[10]),
                    image_url=row[11],
                    is_favorite=bool(row[12]),
                    created_at=datetime.fromisoformat(row[13])
                ))
    return recipes


async def toggle_favorite(recipe_id: int):
    """Переключить статус избранного"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE recipes SET is_favorite = NOT is_favorite WHERE recipe_id = ?",
            (recipe_id,)
        )
        await db.commit()


async def delete_favorite(recipe_id: int):
    """Удалить рецепт из избранного"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM recipes WHERE recipe_id = ?",
            (recipe_id,)
        )
        await db.commit()


async def save_cooking_session(session: CookingSession) -> int:
    """Сохранить сессию готовки"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Удаляем старую сессию пользователя
        await db.execute("DELETE FROM cooking_sessions WHERE user_id = ?", (session.user_id,))
        
        cursor = await db.execute("""
            INSERT INTO cooking_sessions 
            (user_id, recipe_id, current_step, timer_end, is_paused, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session.user_id,
            session.recipe_id,
            session.current_step,
            session.timer_end.isoformat() if session.timer_end else None,
            session.is_paused,
            session.created_at.isoformat(),
            session.updated_at.isoformat()
        ))
        await db.commit()
        return cursor.lastrowid


async def get_cooking_session(user_id: int) -> Optional[CookingSession]:
    """Получить активную сессию готовки"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM cooking_sessions WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return CookingSession(
                    session_id=row[0],
                    user_id=row[1],
                    recipe_id=row[2],
                    current_step=row[3],
                    timer_end=datetime.fromisoformat(row[4]) if row[4] else None,
                    is_paused=bool(row[5]),
                    created_at=datetime.fromisoformat(row[6]),
                    updated_at=datetime.fromisoformat(row[7])
                )
    return None


async def update_cooking_session(session: CookingSession):
    """Обновить сессию готовки"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE cooking_sessions 
            SET current_step = ?, timer_end = ?, is_paused = ?, updated_at = ?
            WHERE session_id = ?
        """, (
            session.current_step,
            session.timer_end.isoformat() if session.timer_end else None,
            session.is_paused,
            datetime.now().isoformat(),
            session.session_id
        ))
        await db.commit()


async def delete_cooking_session(user_id: int):
    """Удалить сессию готовки"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cooking_sessions WHERE user_id = ?", (user_id,))
        await db.commit()


async def add_recipe_to_history(user_id: int, recipe_name: str):
    """Добавить рецепт в историю"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO recipe_history (user_id, recipe_name, created_at)
            VALUES (?, ?, ?)
        """, (user_id, recipe_name, datetime.now().isoformat()))
        await db.commit()


async def get_recent_recipe_names(user_id: int, limit: int = 10) -> List[str]:
    """Получить названия недавних рецептов"""
    names = []
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT recipe_name FROM recipe_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ) as cursor:
            async for row in cursor:
                names.append(row[0])
    return names