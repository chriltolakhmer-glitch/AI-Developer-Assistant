class TokenService:
    def issue(self, username):
        return f"token:{username}"
