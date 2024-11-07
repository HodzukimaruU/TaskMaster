from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings

from django.http import HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_http_methods

from .models import ConfirmationCode, Project, Task
from .forms import RegistrationForm, ProjectForm, TaskForm 

import uuid
import time

@login_required
def index(request):
    return render(request, 'index.html')


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            confirmation_code = str(uuid.uuid4())
            expiration_time = int(time.time()) + settings.CONFIRMATION_CODE_LIFETIME
            ConfirmationCode.objects.create(
                code=confirmation_code, user=user, expiration_time=expiration_time
            )
            
            confirmation_url = settings.SERVER_HOST + reverse("confirm_email") + f"?code={confirmation_code}"
            send_mail(
                'Подтвердите ваш email',
                f'Пожалуйста, подтвердите ваш email по следующей ссылке: {confirmation_url}',
                settings.EMAIL_FROM,
                [user.email],
            )
        return redirect(to="confirm_email_sent")
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})



def confirm_email(request):
    code = request.GET.get('code')
    try:
        confirmation = ConfirmationCode.objects.get(code=code)
        if confirmation.is_expired():
            return HttpResponseBadRequest('Verification code has expired.')
        user = confirmation.user
        user.is_active = True
        user.save()
        confirmation.delete()
        return redirect('login')
    except ConfirmationCode.DoesNotExist:
        return HttpResponseBadRequest('Verification code is invalid.')

@require_http_methods(["GET"])
def confirm_email_stub_controller(request):
    return HttpResponse("Confirmation email sent. Please confirm it by the link.")

def login_view(request):
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

def logout_view(request):
    logout(request)
    return redirect('login')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Project, Task
from .forms import ProjectForm, TaskForm

# Project Views
@login_required
def project_list(request):
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'project_list.html', {'projects': projects})


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            return redirect('project-list')
    else:
        form = ProjectForm()
    return render(request, 'project_form.html', {'form': form})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    tasks = project.tasks.all()
    return render(request, 'project_detail.html', {'project': project, 'tasks': tasks})


@login_required
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project-list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'project_form.html', {'form': form})


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        project.delete()
        return redirect('project-list')
    return render(request, 'project_confirm_delete.html', {'project': project})


# Task View
@login_required
def task_list(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    
    return render(request, 'task_list.html', {'tasks': tasks})


@login_required
def task_create(request):
    project = None
    # Проверяем, передан ли проект в URL
    if 'project' in request.GET:
        project_id = request.GET['project']
        project = Project.objects.get(id=project_id)
    
    # Заполняем форму текущим проектом, если он существует
    form = TaskForm(initial={'project': project}) if project else TaskForm()

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            # Если проект передан, то автоматически связываем его с задачей
            if project:
                task.project = project
            task.assigned_to = request.user  # Присваиваем задачу текущему пользователю
            task.save()
            return redirect('task-list')  # Можно изменить на страницу с задачами

    return render(request, 'task_form.html', {'form': form})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task-list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'task_form.html', {'form': form})

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    return render(request, 'task_detail.html', {'task': task})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('task-list')
    return render(request, 'task_confirm_delete.html', {'task': task})

