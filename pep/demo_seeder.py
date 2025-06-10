import random
from datetime import date, timedelta
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth.models import User

from pep.models import Appointment, Doctor, Note, Patient

def clear_demo_data(doctor):
    user = doctor.user

    if user.is_superuser:
        return  # Segurança extra para não apagar admin

    # Apaga agendamentos do médico
    Appointment.objects.filter(professional=doctor).delete()

    # Apaga notas feitas por esse médico
    Note.objects.filter(professional=user).delete()

    # Apaga o usuário e o Doctor (via on_delete=CASCADE)
    user.delete()

    # Apaga todos os pacientes marcados como demo
    Patient.objects.filter(is_demo=True).delete()


def run_demo_seed(doctor):
    """
    Recebe um médico já criado e gera os 100 pacientes demo.
    """
    for i in range(100):
        name = f"Paciente {i+1}"
        cpf = f"{random.randint(10000000000, 99999999999)}"
        birth_date = date.today() - timedelta(days=random.randint(20*365, 80*365))

        Patient.objects.create(
            name=name,
            cpf=cpf,
            birth_date=birth_date,
            is_demo=True
        )
