import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

MODEL = "HuggingFaceTB/SmolLM3-3B"


# AI API Configuration
AI_API_URL = "https://router.huggingface.co/hf-inference/models/HuggingFaceTB/SmolLM3-3B"
AI_API_TOKEN = os.getenv("AI_API_TOKEN")

# Database
DB_PATH = "data/cooking_bot.db"

# Cooking timer settings
TIMER_CHECK_INTERVAL = 10  # Проверка таймеров каждые 10 секунд

# Recipe generation settings
MAX_RECIPE_ATTEMPTS = 5  # Максимум попыток генерации рецепта
RECIPE_HISTORY_SIZE = 10  # Сколько последних рецептов хранить для избежания повторов

