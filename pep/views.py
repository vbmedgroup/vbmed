from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime, now, make_aware, is_naive
from pep.forms import AppointmentForm, PatientForm, PrescriptionForm
from pep.utils.general import post_login_redirect
from django.conf import settings
from .models import Appointment, Doctor, News, Patient, Note, Prescription
from django.contrib.auth import login, logout
from django.utils import timezone
from operator import attrgetter
import random
from django.contrib import messages
from datetime import time, timedelta, datetime, date
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.utils.crypto import get_random_string
from django.utils.dateparse import parse_date 


# ========================== AUTENTICAÇÃO ==========================
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


# ========================== HOME E DASHBOARD ==========================
@login_required
def home(request):
    all_patients = Patient.objects.only(
        'id', 'name', 'arrival_datetime', 'last_updated', 'last_viewed_at'
    )

    updated_unviewed = []
    new_unviewed = []
    visualized = []

    for p in all_patients:
        time_diff = abs((p.last_updated - p.arrival_datetime).total_seconds())

        p.is_new = time_diff < 5
        p.was_updated = time_diff >= 5
        p.is_visualized = bool(p.last_viewed_at and p.last_viewed_at >= p.last_updated)

        if not p.is_visualized and p.was_updated:
            updated_unviewed.append(p)
        elif not p.is_visualized and p.is_new:
            new_unviewed.append(p)
        else:
            visualized.append(p)

    updated_unviewed.sort(key=attrgetter('last_updated'), reverse=True)
    new_unviewed.sort(key=attrgetter('last_updated'), reverse=True)
    visualized.sort(key=attrgetter('last_updated'), reverse=True)

    recent_patients = updated_unviewed + new_unviewed + visualized

    # Cache da lista de notícias
    news_list = cache.get('news_list')
    if not news_list:
        news_list = News.objects.order_by('-published_at')[:5]
        cache.set('news_list', news_list, 300)  # 5 minutos

    return render(request, 'pep/home.html', {
        'recent_patients': recent_patients,
        'news_list': news_list,
    })
@login_required
def dashboard(request):
    news = News.objects.order_by('-published_at')[:5]
    return render(request, 'pep/home.html', {'news': news})


# ========================== PACIENTES ==========================
@login_required
def patient_profile(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    # Coletando os dados reais do paciente
    evolutions = Note.objects.filter(patient=patient).only('date', 'content')
    prescriptions = Prescription.objects.filter(patient=patient).only('created_at', 'content')
    appointments = Appointment.objects.select_related('professional__user').only(
        'date', 'time', 'type', 'professional__user__first_name'
    ).filter(patient=patient)

    context = {
        'patient': patient,
        'evolutions': evolutions,
        'prescriptions': prescriptions,
        'appointments': appointments,
    }
    return render(request, 'pep/patient_profile.html', context)

@login_required
def patient_list(request):
    patients = Patient.objects.only('id', 'name', 'cpf').order_by('name')
    return render(request, 'pep/patient_list.html', {'patients': patients})

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


# ========================== ANOTAÇÕES (EVOLUÇÕES) ==========================
@login_required
def note_list(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    # Atualiza como visualizado
    patient.last_viewed_at = timezone.now()
    patient.viewed = True
    patient.save()

    notes = Note.objects.filter(patient=patient).only('date', 'content').order_by('-date')

    return render(request, 'pep/note_list.html', {
        'patient': patient,
        'notes': notes,
    })

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


# ========================== AGENDAMENTOS ==========================
def get_available_times(date, professional):
    start = time(8, 0)
    end = time(17, 0)
    interval = timedelta(minutes=30)
    times = []

    now_local = localtime(now())
    is_today = date == now_local.date()
    cutoff_datetime = now_local + timedelta(hours=getattr(settings, 'MIN_HOURS_AHEAD_FOR_APPOINTMENT', 1))

    current = datetime.combine(date, start)
    end_dt = datetime.combine(date, end)

    # Torna 'current' e 'cutoff' ambos aware para evitar comparação inválida
    if is_naive(current):
        current = make_aware(current)
    if is_naive(end_dt):
        end_dt = make_aware(end_dt)

    while current <= end_dt:
        current_time = current.time()

        if is_today and current < cutoff_datetime:
            current += interval
            continue

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
                professional = Doctor.objects.get(pk=selected_doctor_id)

                # Validação extra para garantir que `professional` é realmente um Doctor
                if not isinstance(professional, Doctor):
                    raise TypeError("Profissional inválido.")

                available_times = get_available_times(date_obj, professional)

                if not available_times:
                    messages.error(request, "❌ Não há mais horários disponíveis nesta data.")
            except (Doctor.DoesNotExist, TypeError, ValueError) as e:
                messages.error(request, f"⚠️ Erro ao buscar horários. Verifique a data ou profissional selecionado. ({e})")

    context = {
        'patient': patient,
        'form': form,
        'available_times': available_times,
        'is_doctor': is_doctor,
        'doctor': doctor_instance,
        'selected_date': selected_date,
        'selected_doctor_id': selected_doctor_id,
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
    .only(
        'date', 'time', 'type',
        'patient__name',
        'professional__user__first_name', 'professional__user__last_name'
    ).filter(date=selected_date)

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

@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, 'pep/appointment_detail.html', {
        'appointment': appointment
    })

@login_required
def patient_appointment_list(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)

    # Filtros recebidos
    date = request.GET.get('date')
    professional_id = request.GET.get('professional')

    # Query inicial com joins e carregamento restrito de campos
    appointments = Appointment.objects.select_related('professional__user') \
        .only('date', 'time', 'type', 'professional__user__first_name') \
        .filter(patient=patient)

    if date:
        appointments = appointments.filter(date=date)
    if professional_id:
        appointments = appointments.filter(professional_id=professional_id)

    appointments = appointments.order_by('-date', '-time')

    # Lista de médicos para filtro (com join otimizado)
    professionals = Doctor.objects.select_related('user') \
        .only('id', 'user__first_name', 'user__last_name', 'user__username') \
        .order_by('user__first_name')

    return render(request, 'pep/patient_appointment_list.html', {
        'patient': patient,
        'appointments': appointments,
        'professionals': professionals,
        'selected_date': date,
        'selected_professional': professional_id,
    })


# ========================== PRESCRIÇÕES ==========================
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

@login_required
def prescription_list(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    prescriptions = Prescription.objects.filter(patient=patient).only('created_at', 'content')

    # Filtro por data (GET param: date=YYYY-MM-DD)
    date_str = request.GET.get('date')
    if date_str:
        try:
            date = parse_date(date_str)
            if date:
                prescriptions = prescriptions.filter(created_at__date=date)
        except ValueError:
            pass  # Se a data for inválida, ignora o filtro

    return render(request, 'pep/prescription_list.html', {
        'patient': patient,
        'prescriptions': prescriptions
    })

@login_required
def prescription_detail(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id)
    patient = prescription.patient
    return render(request, 'pep/prescription_detail.html', {
        'prescription': prescription,
        'patient': patient,
    })

@login_required
def prescription_edit(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Prescrição atualizada com sucesso.")
            return redirect('pep:prescription_detail', prescription_id=prescription.id)
        else:
            messages.error(request, "⚠️ Erro ao atualizar prescrição. Verifique os campos.")
    else:
        form = PrescriptionForm(instance=prescription)

    return render(request, 'pep/prescription_form.html', {
        'form': form,
        'patient': prescription.patient,
        'editing': True
    })

@login_required
def prescription_delete(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id)

    if request.method == 'POST':
        patient_id = prescription.patient.id
        prescription.delete()
        messages.success(request, "🗑️ Prescrição excluída com sucesso.")
        return redirect('prescription_list', patient_id=patient_id)

    return render(request, 'pep/prescription_confirm_delete.html', {
        'prescription': prescription,
        'patient': prescription.patient,
    })




