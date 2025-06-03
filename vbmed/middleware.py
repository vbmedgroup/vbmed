from django.shortcuts import redirect
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth import login
from django.contrib.auth import logout
from pep.models import Doctor
from pep.utils.demo import clear_demo_data

# --- Middleware 1: Redireciona usuários não autenticados ---
PROTECTED_PATHS = ['/pep/']
EXCLUDED_PATHS = ['/teste_finalizado/', '/pep/testar/', '/static/', '/media/']

class TesteFinalizadoRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if (
            not request.user.is_authenticated and
            any(path.startswith(p) for p in PROTECTED_PATHS) and
            not any(path.startswith(p) for p in EXCLUDED_PATHS)
        ):
            return redirect('/teste_finalizado/')

        return self.get_response(request)

# --- Middleware 2: Limpa e recria dados demo após 30 min do login ---
class DemoAutoResetMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        EXCLUDED_PATHS = ['/teste_finalizado/', '/pep/testar/', '/static/', '/media/']

        if any(path.startswith(p) for p in EXCLUDED_PATHS):
            return self.get_response(request)

        user = request.user

        if user.is_authenticated:
            doctor = getattr(user, 'doctor', None)
            if doctor and doctor.is_demo:
                if doctor.created_at and (now() - doctor.created_at) > timedelta(minutes=30):
                    clear_demo_data(doctor)
                    logout(request)  # ✅ Desloga o usuário
                    return redirect('/teste_finalizado/')

        return self.get_response(request)