from django import forms
from .models import Appointment, Doctor, Patient, Prescription
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import datetime

#Formulário para gerar novo paciente
from django import forms
from pep.models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'name',
            'birth_date',
            'phone',
            'cpf',
            'address_street',
            'address_number',
            'address_complement',
            'address_city',
            'address_state',
            'address_zipcode',
            'visit_reason',
            'visit_type',
            'last_visit',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'last_visit': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'visit_reason': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
                'style': (
                    'width: 100%; padding: 12px; border: 1px solid #ccc; '
                    'border-radius: 6px; font-size: 14px;'
                )
            })


#Formulário para novo agendamento
class AppointmentForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Data"
    )

    type = forms.ChoiceField(
        choices=Appointment.APPOINTMENT_TYPE_CHOICES,
        label="Tipo"
    )

    class Meta:
        model = Appointment
        fields = ['date', 'professional', 'type']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Se for médico logado, remove o campo 'professional'
        if self.user and Doctor.objects.filter(user=self.user).exists():
            self.fields.pop('professional')
        else:
            self.fields['professional'].queryset = Doctor.objects.select_related('user').all()

    def clean_date(self):
        selected_date = self.cleaned_data.get('date')
        if selected_date < now().date():
            raise forms.ValidationError("Não é possível agendar para uma data no passado.")
        return selected_date
    


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Digite aqui a prescrição...'}),
        }
        labels = {
            'content': 'Prescrição médica',
        }
