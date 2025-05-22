from django.contrib import messages
from django.shortcuts import redirect, render
from django.core.mail import send_mail
from website.forms import ContactForm

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def services(request):
    return render(request, 'services.html')

def contact(request):
    return render(request, 'contact.html')

def contact_view(request):
    form = ContactForm()
    
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            nome = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            mensagem = form.cleaned_data["message"]
            
            # Enviar o e-mail
            send_mail(
                f"Mensagem de {nome}",
                mensagem,
                email,  # E-mail do remetente
                ['seuemail@dominio.com'],  # Substitua pelo seu e-mail de recebimento
                fail_silently=False,
            )
            
            messages.success(request, "Sua mensagem foi enviada com sucesso!")
            form = ContactForm()  # Resetando o formulário após envio

    return render(request, "contact.html", {"form": form})


def teste_finalizado(request):
    return render(request, 'teste_finalizado.html')