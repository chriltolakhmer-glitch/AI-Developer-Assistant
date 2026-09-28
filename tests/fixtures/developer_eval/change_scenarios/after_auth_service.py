from src.auth.token_service import TokenService

class AuthService:
    def authenticate(self, username):
        return TokenService().issue(username)
