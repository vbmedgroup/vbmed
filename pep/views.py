from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime, now, make_aware
from collections import defaultdict
from pep.forms import AppointmentForm, PatientForm, PrescriptionForm
from pep.utils.general import post_login_redirect
from .models import Appointment, Doctor, News, Patient, Note, Prescription
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from datetime import datetime
from django.utils import timezone
import random
from django.contrib import messages
from datetime import time, timedelta, datetime, date
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string


def user_login(request):
    if request.user.is_authenticated:
        return redirect('pep:home')  # ou post_login_redirect(request)

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return post_login_redirect(request)
    else:
        form = AuthenticationForm()

    return render(request, 'pep/login.html', {'form': form})


def test_drive_view(request):
    agora = timezone.now()
    tempo_limite = agora - timedelta(minutes=30)

    # Tenta encontrar um médico demo criado nos últimos 30 minutos
    doctor = Doctor.objects.filter(is_demo=True, created_at__gte=tempo_limite).first()

    if doctor:
        # Já existe demo válido → login automático
        login(request, doctor.user)
        return post_login_redirect(request)

    # Caso não exista, limpa os dados antigos (se ainda restarem)
    Doctor.objects.filter(is_demo=True).delete()
    Patient.objects.filter(is_demo=True).delete()

    # Geração de novo médico e paciente demo
    username = f"demo_{get_random_string(8)}"
    password = get_random_string(12)
    email = f"{username}@teste.com"

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name="Demo",
        last_name="User"
    )

    doctor = Doctor.objects.create(
        user=user,
        crm="0000-DEMO",
        specialty="Clínico Geral",
        is_demo=True,
        created_at=agora
    )

    # Criação de 10 pacientes fictícios
    for i in range(10):
        name = f"Paciente {i+1}"
        cpf = f"{random.randint(10000000000, 99999999999)}"
        birth_date = date.today() - timedelta(days=random.randint(20*365, 80*365))

        Patient.objects.create(
            name=name,
            cpf=cpf,
            birth_date=birth_date,
            is_demo=True
        )

    login(request, user)
    return post_login_redirect(request)


def user_logout(request):
    logout(request)
    return redirect("/teste_finalizado/")

# Home 
@login_required
def home(request):
    recent_unviewed = Patient.objects.filter(viewed=False).order_by('last_updated')
    recent_viewed = Patient.objects.filter(viewed=True).order_by('last_updated')
    recent_patients = list(recent_unviewed) + list(recent_viewed)

    # Lógica refinada para identificar status dos cards
    for p in recent_patients:
        time_diff = abs((p.last_updated - p.arrival_datetime).total_seconds())

        p.is_new = time_diff < 5  # considerado novo se criado recentemente
        p.was_updated = time_diff >= 5  # atualizado se houve modificação relevante
        p.is_visualized = p.last_viewed_at and p.last_viewed_at >= p.last_updated

    news_list = News.objects.order_by('-published_at')

    return render(request, 'pep/home.html', {
        'recent_patients': recent_patients,
        'news_list': news_list,
    })


def patient_profile(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    # Coletando os dados reais do paciente
    evolutions = Note.objects.filter(patient=patient)
    prescriptions = Prescription.objects.filter(patient=patient)
    appointments = Appointment.objects.filter(patient=patient)

    context = {
        'patient': patient,
        'evolutions': evolutions,
        'prescriptions': prescriptions,
        'appointments': appointments,
    }
    return render(request, 'pep/patient_profile.html', context)


@login_required
def patient_list(request):
    patients = Patient.objects.all().order_by('name')
    return render(request, 'pep/patient_list.html', {'patients': patients})

# Adicionar novo paciente
@login_required
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)

            # Se for médico em modo de demonstração, marcar o paciente como demo
            if hasattr(request.user, 'doctor') and request.user.doctor.is_demo:
                patient.is_demo = True

            patient.save()
            return redirect('pep:home')  # ou 'pep:patient_list'
    else:
        form = PatientForm()

    return render(request, 'pep/patient_create.html', {'form': form})

@login_required
def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    form = PatientForm(request.POST or None, instance=patient)

    if request.method == 'POST' and form.is_valid():
        form.save()
        # 🔁 Marcar como não visualizado
        patient.viewed = False
        patient.save()
        return redirect('pep:patient_list')

    return render(request, 'pep/patient_form.html', {'form': form})

# Evoluções do paciente
@login_required
def note_list(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    # Marca o paciente como visualizado (remove borda da home)
    if not patient.viewed:
        patient.viewed = True
        patient.save()

    notes = Note.objects.filter(patient=patient).order_by('-date')

    # Agrupamento por data
    grouped_notes = defaultdict(list)
    for note in notes:
        note_date = localtime(note.date).date()
        grouped_notes[note_date].append(note)

    sorted_dates = sorted(grouped_notes.keys(), reverse=True)

    return render(request, 'pep/note_list.html', {
        'patient': patient,
        'grouped_notes': grouped_notes,
        'sorted_dates': sorted_dates,
    })

# Nova evolução
@login_required
def note_create(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    notes = Note.objects.filter(patient=patient).order_by('-date')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Note.objects.create(
                patient=patient,
                professional=request.user,
                content=content
            )
            return redirect('pep:note_create', patient_id=patient.id)

    return render(request, 'pep/note_create.html', {
        'patient': patient,
        'notes': notes
    })

@login_required
def note_detail(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    return render(request, 'pep/note_detail.html', {'note': note})

@login_required
def note_day_detail(request, patient_id, date):
    patient = get_object_or_404(Patient, id=patient_id)
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    notes = Note.objects.filter(patient=patient, date__date=date_obj).order_by('date')
    return render(request, 'pep/note_day_detail.html', {'notes': notes, 'patient': patient, 'date': date_obj})

@login_required
def fill_section(request, patient_id, section):
    patient = get_object_or_404(Patient, pk=patient_id)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Note.objects.create(
                patient=patient,
                professional=request.user,
                content=f"{section.upper()}:\n{content}"
            )
            # 🔁 Marcar como não visualizado e atualizar o timestamp
            patient.viewed = False
            patient.last_updated = timezone.now()
            patient.save()

            return redirect('pep:note_create', patient_id=patient.id)

    return render(request, 'pep/note_create.html', {
        'patient': patient,
        'section': section
    })




def get_available_times(date, professional):
    start = time(8, 0)
    end = time(17, 0)
    interval = timedelta(minutes=30)
    times = []

    current = datetime.combine(date, start)
    end_dt = datetime.combine(date, end)

    now_local = localtime(now())
    is_today = date == now_local.date()

    while current <= end_dt:
        current_time = current.time()

        # Oculta horários passados se a data for hoje
        if is_today and datetime.combine(date, current_time) < now_local:
            current += interval
            continue

        # Verifica se o horário está livre
        if not Appointment.objects.filter(professional=professional, date=date, time=current_time).exists():
            times.append(current_time)

        current += interval

    return times

@login_required
def schedule_appointment(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    user = request.user

    is_doctor = Doctor.objects.filter(user=user).exists()
    doctor_instance = Doctor.objects.get(user=user) if is_doctor else None

    available_times = []
    selected_date = None
    selected_doctor_id = None

    if request.method == 'POST':
        data = request.POST.copy()
        selected_date = data.get('date')
        selected_time = data.get('time')
        selected_doctor_id = data.get('professional') if not is_doctor else doctor_instance.id

        if is_doctor:
            data['professional'] = doctor_instance.id

        form = AppointmentForm(data, user=user)

        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.time = selected_time

            if is_doctor:
                appointment.professional = doctor_instance

            # Verifica se está agendando para o passado
            appointment_datetime_str = f"{appointment.date} {appointment.time}"
            try:
                appointment_datetime_naive = datetime.strptime(appointment_datetime_str, "%Y-%m-%d %H:%M")
                appointment_datetime = make_aware(appointment_datetime_naive)

                if appointment_datetime < now():
                    messages.error(request, "❌ Não é possível agendar em data ou horário anterior ao momento atual.")
                else:
                    conflict = Appointment.objects.filter(
                        professional=appointment.professional,
                        date=appointment.date,
                        time=appointment.time
                    ).exists()

                    if conflict:
                        messages.error(request, "❌ Este horário já está agendado para o profissional selecionado.")
                    else:
                        appointment.save()
                        messages.success(request, "✅ Agendamento realizado com sucesso.")
                        return redirect('pep:note_create', patient_id=patient.id)
            except ValueError:
                messages.error(request, "❌ Data ou hora em formato inválido.")
        else:
            messages.error(request, "⚠️ Dados inválidos. Verifique o formulário.")
    else:
        selected_date = request.GET.get('date')
        selected_doctor_id = request.GET.get('professional') if not is_doctor else (
            doctor_instance.id if doctor_instance else None
        )

        form = AppointmentForm(user=user, initial={
            'date': selected_date,
            'professional': selected_doctor_id
        })

        if selected_date and selected_doctor_id:
            try:
                date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
                professional = get_object_or_404(Doctor, pk=selected_doctor_id)
                available_times = get_available_times(date_obj, professional)

                if not available_times:
                    messages.error(request, "❌ Não há mais horários disponíveis nesta data.")
            except Exception:
                messages.error(request, "⚠️ Erro ao buscar horários. Verifique a data ou profissional selecionado.")

    context = {
        'patient': patient,
        'form': form,
        'available_times': available_times,
        'is_doctor': is_doctor,
        'doctor': doctor_instance,
    }
    return render(request, 'pep/schedule_appointment.html', context)


@login_required
def appointment_list(request):
    user = request.user
    is_doctor = Doctor.objects.filter(user=user).exists()
    doctor_instance = Doctor.objects.get(user=user) if is_doctor else None

    # Filtros GET
    date_str = request.GET.get('date') or timezone.localdate().isoformat()
    professional_id = request.GET.get('professional') if not is_doctor else (doctor_instance.id if doctor_instance else None)

    selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    appointments = Appointment.objects.select_related('patient', 'professional__user') \
                                      .filter(date=selected_date)

    if professional_id:
        appointments = appointments.filter(professional__id=professional_id)

    appointments = appointments.order_by('time')

    doctors = Doctor.objects.select_related('user').all() if not is_doctor else None

    return render(request, 'pep/appointment_list.html', {
        'appointments': appointments,
        'today': selected_date,
        'doctors': doctors,
        'is_doctor': is_doctor,
        'selected_professional_id': professional_id
    })

def patient_appointment_list(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    appointments = Appointment.objects.filter(patient=patient).order_by('-date', '-time')

    return render(request, 'pep/patient_appointment_list.html', {
        'patient': patient,
        'appointments': appointments,
    })


@login_required
def create_prescription(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.patient = patient
            prescription.doctor = doctor
            prescription.save()
            messages.success(request, "✅ Prescrição registrada com sucesso.")
            return redirect('pep:patient_profile', pk=patient.id)
        else:
            messages.error(request, "❌ Corrija os erros no formulário.")
    else:
        form = PrescriptionForm()

    return render(request, 'pep/create_prescription.html', {
        'form': form,
        'patient': patient,
    })

def prescription_list(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')

    return render(request, 'pep/prescription_list.html', {
        'patient': patient,
        'prescriptions': prescriptions
    })


@login_required
def dashboard(request):
    news = News.objects.order_by('-published_at')[:5]
    return render(request, 'pep/home.html', {'news': news})


