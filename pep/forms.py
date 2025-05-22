from django import forms
from .models import Appointment, Doctor, Patient
from django.contrib.auth.models import User

#Formulário para gerar novo paciente
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'name', 'birth_date', 'phone',
            'address_street', 'address_number', 'address_complement',
            'address_city', 'address_state', 'address_zipcode',
            'visit_reason'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'visit_reason': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
                'style': 'width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px;'
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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Se for médico logado, remove o campo 'professional'
        if user and Doctor.objects.filter(user=user).exists():
            self.fields.pop('professional')
        else:
            # Caso seja recepção, exibe a lista de médicos
            self.fields['professional'].queryset = Doctor.objects.select_related('user').all()