from django.contrib import admin
from pep.models import News, Doctor


#Registra o feed de notícias no admin
admin.site.register(News)


#Registra médicos no admin
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'crm', 'specialty']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'crm']

