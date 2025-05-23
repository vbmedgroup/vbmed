import traceback
from django.http import HttpResponseServerError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime
from collections import defaultdict
from pep.forms import AppointmentForm, PatientForm
from .models import Appointment, Doctor, News, Patient, Note
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from datetime import datetime
from django.utils import timezone
from django.contrib import messages
from datetime import time, timedelta, datetime
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect


# Login view
def user_login(request):
    if request.user.is_authenticated:
        return redirect('pep:patient_list')

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('pep:home')
    else:
        form = AuthenticationForm()

    return render(request, 'pep/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect("/teste_finalizado/")

# Home 
@login_required
def home(request):
    recent_unviewed = Patient.objects.filter(viewed=False).order_by('last_updated')
    recent_viewed = Patient.objects.filter(viewed=True).order_by('last_updated')
    recent_patients = list(recent_unviewed) + list(recent_viewed)

    news_list = News.objects.order_by('-published_at')

    return render(request, 'pep/home.html', {
        'recent_patients': recent_patients,
        'news_list': news_list,
    })
    


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
            form.save()
            return redirect('pep:home')  # ou 'patient_list'
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

    while current <= end_dt:
        if not Appointment.objects.filter(professional=professional, date=date, time=current.time()).exists():
            times.append(current.time())
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
        selected_doctor_id = data.get('professional') if not is_doctor else doctor_instance.id
        selected_time = data.get('time')

        if is_doctor:
            data['professional'] = doctor_instance.id

        form = AppointmentForm(data, user=user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.time = selected_time

            if is_doctor:
                appointment.professional = doctor_instance

            # Verifica conflito
            conflict = Appointment.objects.filter(
                professional=appointment.professional,
                date=appointment.date,
                time=appointment.time
            ).exists()

            if conflict:
                messages.error(request, "Este horário já está agendado para o profissional selecionado.")
            else:
                appointment.save()
                messages.success(request, "Agendamento realizado com sucesso.")
                return redirect('pep:note_create', patient_id=patient.id)
        else:
            messages.error(request, "Por favor, corrija os erros do formulário.")
    else:
        selected_date = request.GET.get('date')
        selected_doctor_id = request.GET.get('professional') if not is_doctor else (doctor_instance.id if doctor_instance else None)

        form = AppointmentForm(user=user, initial={
            'date': selected_date,
            'professional': selected_doctor_id
        })

        if selected_date and selected_doctor_id:
            try:
                date = datetime.strptime(selected_date, "%Y-%m-%d").date()
                professional = get_object_or_404(Doctor, pk=selected_doctor_id)
                available_times = get_available_times(date, professional)
            except Exception:
                pass

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


# Retirar ou comentar em produção
@login_required
def pep_reset_and_exit(request):
    # Apagar tudo
    Patient.objects.all().delete()
    Note.objects.all().delete()
    
    # Logout do usuário
    logout(request)
    
    # Redirecionar de volta para o site
    return redirect("/teste_finalizado/")  # coloque aqui a URL real do seu site


@login_required
def dashboard(request):
    news = News.objects.order_by('-published_at')[:5]
    return render(request, 'pep/home.html', {'news': news})


