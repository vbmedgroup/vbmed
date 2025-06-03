from django.urls import path
from vbmed import settings
from . import views
from django.conf.urls.static import static

app_name = "pep"

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('', views.home, name='home'),
    path('testar/', views.test_drive_view, name='testar'),
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/new/', views.patient_create, name='patient_create'),
    path('patients/<int:patient_id>/notes/', views.note_list, name='note_list'),
    path('patients/<int:patient_id>/notes/new/', views.note_create, name='note_create'),
    path('notes/<int:note_id>/', views.note_detail, name='note_detail'),
    path('notes/<int:patient_id>/date/<str:date>/', views.note_day_detail, name='note_day_detail'),
    path('preencher/<int:patient_id>/<str:section>/', views.fill_section, name='fill_section'),
    path('pacientes/<int:patient_id>/agendar/', views.schedule_appointment, name='schedule_appointment'),
    path('agendamentos/', views.appointment_list, name='appointment_list'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)