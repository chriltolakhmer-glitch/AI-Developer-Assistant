from src.utils.formatting import format_token


class TokenManager:
    def issue(self, username, settings):
        raw_token = f"{username}:{settings['issuer']}"
        return format_token(raw_token)
