from django.utils.timezone import now
from datetime import timedelta
from pep.models import Appointment, Note, Patient, Doctor

def clear_demo_data(doctor):
    user = doctor.user

    if user.is_superuser:
        return  # Segurança extra para não apagar admin

    # Apaga agendamentos do médico
    Appointment.objects.filter(professional=doctor).delete()

    # Apaga notas feitas por esse médico
    Note.objects.filter(professional=user).delete()

    # Apaga todos os pacientes marcados como demo
    Patient.objects.filter(is_demo=True).delete()

    # Por segurança, não apagamos o user/doctor aqui. Isso é feito no middleware.
    # Se quiser apagar o médico aqui, basta descomentar:
    # user.delete()

def create_demo_data(doctor):
    """
    Cria os 100 pacientes demo para o médico fornecido.
    """
    from pep.demo_seeder import run_demo_seed
    run_demo_seed(doctor)
