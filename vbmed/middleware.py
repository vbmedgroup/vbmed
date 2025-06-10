from django.shortcuts import redirect
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth import logout
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

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

# --- Middleware 2: Limpa e redireciona após 30 minutos ---
class DemoAutoResetMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = request.path

        if any(path.startswith(p) for p in EXCLUDED_PATHS):
            return None

        user = request.user
        if not user.is_authenticated:
            return None

        doctor = getattr(user, 'doctor', None)

        if doctor and doctor.is_demo:
            if doctor.created_at and (now() - doctor.created_at) > timedelta(minutes=30):
                clear_demo_data(doctor)
                logout(request)
                return redirect(reverse('teste_finalizado'))

        return None
