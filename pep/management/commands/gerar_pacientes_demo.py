from django.core.management.base import BaseCommand
from pep.models import Patient
from faker import Faker
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Gera 100 pacientes fictícios para demonstração'

    def handle(self, *args, **options):
        fake = Faker('pt_BR')
        motivos = ['emergency', 'surgery', 'scheduled_exam', 'consultation', 'other']
        estados = ['SP', 'RJ', 'MG', 'BA', 'PR', 'RS', 'SC', 'PE', 'CE', 'GO']

        for _ in range(100):
            nome = fake.name()
            nascimento = fake.date_of_birth(minimum_age=18, maximum_age=90)
            telefone = fake.phone_number()
            rua = fake.street_name()
            numero = str(fake.building_number())
            complemento = random.choice(["Fundos", "Apto 101", "Sala 3", "Casa 2", "Bloco B", "Sem complemento"])
            cidade = fake.city()
            estado = random.choice(estados)
            cep = fake.postcode()
            motivo = random.choice(motivos)
            agora = datetime.now()
            ultima_visita = agora - timedelta(days=random.randint(30, 600))

            Patient.objects.create(
                name=nome,
                birth_date=nascimento,
                phone=telefone,
                address_street=rua,
                address_number=numero,
                address_complement=complemento,
                address_city=cidade,
                address_state=estado,
                address_zipcode=cep,
                viewed=False,
                visit_reason=motivo,
                arrival_datetime=agora,
                last_updated=agora,
                visit_type='Ambulatorial',
                last_visit=ultima_visita
            )

        self.stdout.write(self.style.SUCCESS('✅ 100 pacientes de demonstração criados com sucesso!'))
