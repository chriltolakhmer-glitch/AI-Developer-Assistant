from src.auth.token import TokenManager

class AuthService:
    def login(self, username):
        return TokenManager().issue(username)
