from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния для регистрации"""
    name = State()
    goal = State()
    dietary_restrictions = State()
    equipment = State()


class ProfileStates(StatesGroup):
    """Состояния для редактирования профиля"""
    edit_name = State()
    edit_goal = State()
    edit_restrictions = State()
    edit_equipment = State()


class RecipeStates(StatesGroup):
    """Состояния для создания рецепта"""
    request = State()
    ingredients = State()
    confirm = State()