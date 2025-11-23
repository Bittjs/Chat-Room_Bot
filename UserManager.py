from config import users

class UserStates:
    NONE = "none"
    CHAT = "chat"
    SETTING_NAME = "setting_name"
    CREATING_ROOM = "creating_room"
    CONFIRMING = "confirming"

class UserManager:
    """Управление пользователями и их состояниями"""
    def __init__(self):
        self.users: dict[int, str] = users  # user_id -> username
        self.states: dict[int, str] = {}  # user_id -> state
        self.temp_data: dict[int, dict] = {}  # user_id -> temporary data

    def register_user(self, user_id: int, username: str) -> None:
        """Зарегистрировать пользователя"""
        self.users[user_id] = username

    def update_username(self, user_id: int, new_username: str) -> str:
        old_username = self.users.get(user_id, "Неизвестный")
        self.users[user_id] = new_username
        return old_username

    def get_username(self, user_id: int) -> str:
        return self.users.get(user_id, "Неизвестный")

    def is_registered(self, user_id: int) -> bool:
        return user_id in self.users

    def set_state(self, user_id: int, state: str) -> None:
        self.states[user_id] = state

    def get_state(self, user_id: int) -> str:
        return self.states.get(user_id, UserStates.NONE)