from src.auth.token import TokenManager
from src.config import load_auth_config

class AuthService:
    def login(self, username, password):
        settings = load_auth_config()
        return TokenManager().issue(username, settings)
