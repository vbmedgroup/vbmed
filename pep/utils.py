from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils.timezone import now
from django.contrib import messages
from datetime import timedelta

def post_login_redirect(request):
    user = request.user

    # Verificação de médico
    if hasattr(user, 'doctor'):
        doctor = user.doctor
        if doctor.is_demo:
            expiration = doctor.created_at + timedelta(hours=1)
            if now() > expiration:
                logout(request)
                messages.error(request, "Seu tempo de demonstração expirou.")
                return redirect('teste_finalizado')
        return redirect('pep:patient_list')  # ou seu dashboard médico

    # Exemplo para futura recepção:
    # elif hasattr(user, 'receptionist'):
    #     return redirect('dashboard_recepcao')

    # Fallback
    return redirect('pep:home')
