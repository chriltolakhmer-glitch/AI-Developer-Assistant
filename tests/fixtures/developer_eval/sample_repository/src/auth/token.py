class TokenManager:
    def issue(self, username, settings):
        return f"token:{username}:{settings['issuer']}"
