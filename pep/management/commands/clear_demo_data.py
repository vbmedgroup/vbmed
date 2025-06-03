from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from pep.models import Appointment, Note, Doctor, Patient

class Command(BaseCommand):
    help = 'Remove dados criados por médicos em modo de demonstração após 1 hora'

    def handle(self, *args, **kwargs):
        expired_demos = Doctor.objects.filter(is_demo=True)

        for doctor in expired_demos:
            user = doctor.user

            if user.is_superuser:
                self.stdout.write(f"⚠️ Ignorando superusuário: {user.username}")
                continue

            self.stdout.write(f"🧹 Limpando dados do médico demo: {doctor}")

            # Apagar agendamentos ligados ao médico
            Appointment.objects.filter(professional=doctor).delete()

            # Apagar notas feitas por esse médico
            Note.objects.filter(professional=user).delete()

            # Apagar o usuário e o médico
            user.delete()  # Isso também apaga o Doctor via on_delete=CASCADE

        # Apagar pacientes marcados como demo
        deleted, _ = Patient.objects.filter(is_demo=True).delete()
        self.stdout.write(f"🧹 Pacientes demo apagados: {deleted}")

        self.stdout.write("✅ Limpeza concluída.")
