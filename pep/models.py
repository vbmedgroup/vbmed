from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.utils import timezone

#Pacientes e médicos ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#Modelo de Paiciente
from django.db import models
from django.utils.timezone import now

class Patient(models.Model):
    VISIT_REASON_CHOICES = [
        ('emergency', 'Emergência'),
        ('surgery', 'Cirurgia'),
        ('scheduled_exam', 'Exame Agendado'),
        ('consultation', 'Consulta'),
        ('other', 'Outro'),
    ]

    name = models.CharField("Nome completo", max_length=100)
    birth_date = models.DateField("Data de nascimento")
    phone = models.CharField("Telefone", max_length=20, blank=True)
    cpf = models.CharField("CPF", max_length=14, blank=True, null=True)
    address_street = models.CharField("Rua", max_length=150)
    address_number = models.CharField("Número", max_length=10)
    address_complement = models.CharField("Complemento", max_length=50, blank=True)
    address_city = models.CharField("Cidade", max_length=100)
    address_state = models.CharField("Estado", max_length=50)
    address_zipcode = models.CharField("CEP", max_length=20)

    visit_reason = models.CharField("Motivo da visita", max_length=20, choices=VISIT_REASON_CHOICES)
    arrival_datetime = models.DateTimeField("Data/Hora de chegada", auto_now_add=True)
    last_updated = models.DateTimeField("Última atualização", default=now)
    last_viewed_at = models.DateTimeField("Visualizado em", blank=True, null=True)  # 🆕 Campo adicionado

    viewed = models.BooleanField(default=False)
    visit_type = models.CharField("Tipo de atendimento", max_length=100, blank=True, null=True)
    last_visit = models.DateTimeField("Data da última consulta", blank=True, null=True)
    is_demo = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    

# Modelo de médico
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    crm = models.CharField(max_length=20, blank=True, null=True)
    specialty = models.CharField(max_length=100, blank=True, null=True)

    # Adições:
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



class Appointment(models.Model):
    CONSULTA = 'consulta'
    EXAME = 'exame'

    APPOINTMENT_TYPE_CHOICES = [
        (CONSULTA, 'Consulta'),
        (EXAME, 'Exame'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    professional = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('professional', 'date', 'time')  # impede conflitos de horário

    def __str__(self):
        return (
            f"{self.patient.name} - {self.get_type_display()} em {self.date} às {self.time} "
            f"com {self.professional.user.get_full_name()}"
        )



class Note(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='notes')
    professional = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return f"{self.patient.name} - {self.date}"
    
class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

