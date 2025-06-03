from django.utils.timezone import now
from datetime import timedelta
from pep.models import Appointment, Note, Patient, Doctor

def clear_demo_data(doctor):
    user = doctor.user

    if user.is_superuser:
        return

    Appointment.objects.filter(professional=doctor).delete()
    Note.objects.filter(professional=user).delete()
    Patient.objects.filter(is_demo=True).delete()
    # Se quiser apagar o próprio médico, comente:
    # user.delete()

def create_demo_data(doctor):
    # Reaproveite aqui sua lógica que cria os 1000 pacientes, etc.
    # Exemplo:
    from pep.utils import run_demo_seed
    run_demo_seed(doctor)
