from src.auth.service import AuthService

def login_route(request):
    return AuthService().login(request.user, request.password)
