from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('pep', '0002_news_patient_last_visit_patient_visit_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='address_street',
            field=models.CharField(max_length=150, default=''),
        ),
        migrations.AddField(
            model_name='patient',
            name='address_number',
            field=models.CharField(max_length=10, default=''),
        ),
        migrations.AddField(
            model_name='patient',
            name='address_complement',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='address_city',
            field=models.CharField(max_length=100, default=''),
        ),
        migrations.AddField(
            model_name='patient',
            name='address_state',
            field=models.CharField(max_length=50, default=''),
        ),
        migrations.AddField(
            model_name='patient',
            name='address_zipcode',
            field=models.CharField(max_length=20, default='00000-000'),
        ),
        migrations.AddField(
            model_name='patient',
            name='visit_reason',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('emergency', 'Emergência'),
                    ('surgery', 'Cirurgia'),
                    ('scheduled_exam', 'Exame Agendado'),
                    ('consultation', 'Consulta'),
                    ('other', 'Outro'),
                ],
                default='other',
            ),
        ),
    ]
