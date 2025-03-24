from django.urls import path
from . import views
from .views import contact_view

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', contact_view, name='contact'),
]
