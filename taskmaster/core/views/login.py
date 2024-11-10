from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Incorrect username or password.')
        else:
            messages.error(request, 'Incorrect data. Please check and try again.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect('login')
