from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.conf import settings

from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseForbidden, Http404
from django.views.decorators.http import require_http_methods

from .models import ConfirmationCode, Project, Task, ProjectInvitation, ProjectMembership, ProjectChatMessage, TaskAssignmentNotification
from .forms import RegistrationForm, ProjectForm, TaskForm, ProjectInvitationForm

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


# Project Views
@login_required
def project_list(request):
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(members=request.user)
    ).distinct()
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


def get_user_role_in_project(user, project):
    try:
        membership = ProjectMembership.objects.get(user=user, project=project)
        return membership.role
    except ProjectMembership.DoesNotExist:
        return None


@login_required
def project_detail(request, pk):
    project = Project.objects.filter(
        Q(pk=pk) & (Q(owner=request.user) | Q(members=request.user))
    ).distinct().first()
    
    if not project:
        raise Http404("Проект не найден или у вас нет доступа.")

    role = get_user_role_in_project(request.user, project)
    tasks = project.tasks.all()
    is_owner = request.user == project.owner
    
    return render(request, 'project_detail.html', {
        'project': project,
        'tasks': tasks,
        'role': role,
        'is_owner': is_owner
    })


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

@login_required
def project_participants(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if project.owner != request.user and not project.members.filter(id=request.user.id).exists():
        raise PermissionDenied("У вас нет доступа к этому проекту.")

    participants = ProjectMembership.objects.filter(project=project)

    if project.owner not in [membership.user for membership in participants]:
        participants = list(participants)
        participants.insert(0, ProjectMembership(project=project, user=project.owner, role='owner'))

    return render(request, 'project_participants.html', {
        'project': project,
        'participants': participants
    })


@login_required
def project_chat(request, project_id):
    project = Project.objects.get(pk=project_id)

    if not ProjectMembership.objects.filter(project=project, user=request.user).exists() and project.owner != request.user:
        raise PermissionDenied("У вас нет доступа к чату этого проекта.")

    messages = ProjectChatMessage.objects.filter(project=project).order_by('created_at')

    if request.method == "POST":
        message_text = request.POST.get("message")
        if message_text:
            ProjectChatMessage.objects.create(project=project, user=request.user, message=message_text)
    
    return render(request, 'project_chat.html', {
        'project': project,
        'messages': messages
    })

# Task View
@login_required
def task_list(request):
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(members=request.user)
    ).distinct()

    tasks_for_projects = Task.objects.filter(
        Q(project__in=projects)
    ).distinct()

    tasks_without_project = Task.objects.filter(
        Q(assigned_to=request.user) & Q(project__isnull=True)
    ).distinct()

    status = request.GET.get("status")
    priority = request.GET.get("priority")
    
    if status:
        tasks_for_projects = tasks_for_projects.filter(status=status)
        tasks_without_project = tasks_without_project.filter(status=status)
    if priority:
        tasks_for_projects = tasks_for_projects.filter(priority=priority)
        tasks_without_project = tasks_without_project.filter(priority=priority)
    
    projects_with_tasks = {}
    for task in tasks_for_projects:
        if task.project not in projects_with_tasks:
            projects_with_tasks[task.project] = []
        projects_with_tasks[task.project].append(task)
    
    return render(request, 'task_list.html', {
        'tasks_for_projects': tasks_for_projects,
        'tasks_without_project': tasks_without_project,
        'projects_with_tasks': projects_with_tasks
    })

@login_required
def task_create(request):
    project = None
    if 'project' in request.GET:
        project_id = request.GET['project']
        project = get_object_or_404(Project, id=project_id)

    if project:
        role = get_user_role_in_project(request.user, project)
        if role != 'editor' and request.user != project.owner:
            raise PermissionDenied("У вас нет прав для добавления задач в этом проекте.")

    form = TaskForm(initial={'project': project}, project=project, hide_assigned=not project)

    if request.method == 'POST':
        form = TaskForm(request.POST, project=project, hide_assigned=not project)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            if not project and not task.assigned_to:
                task.assigned_to = request.user
            if project:
                task.project = project
            task.save()

            if task.project and task.assigned_to:
                TaskAssignmentNotification.objects.create(task=task, user=task.assigned_to)

            return redirect('task-list')

    return render(request, 'task_form.html', {'form': form})

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    hide_assigned = task.project is None
    project = task.project

    if project:
        role = get_user_role_in_project(request.user, project)
        if role not in ['viewer', 'editor'] and request.user != project.owner:
            raise PermissionDenied("У вас нет прав для редактирования этой задачи.")
    else:
        if request.user != task.owner:
            raise PermissionDenied("У вас нет прав для редактирования этой задачи.")

    form = TaskForm(instance=task, project=project, hide_assigned=hide_assigned)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, project=project, hide_assigned=hide_assigned)
        if form.is_valid():
            old_assigned_user = task.assigned_to
            task = form.save()

            if task.project and task.assigned_to:
                TaskAssignmentNotification.objects.create(task=task, user=task.assigned_to)

            return redirect('task-detail', pk=task.pk)

    return render(request, 'task_form.html', {'form': form})



@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)

    role = None

    if task.project:
        role = get_user_role_in_project(request.user, task.project)
        if role not in ['viewer', 'editor'] and request.user != task.project.owner:
            return HttpResponseForbidden("У вас нет доступа к этой задаче.")
    else:
        if request.user != task.owner and request.user != task.assigned_to:
            return HttpResponseForbidden("У вас нет доступа к этой задаче.")

    return render(request, 'task_detail.html', {'task': task, 'role': role})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    role = get_user_role_in_project(request.user, project)

    if request.user != task.assigned_to and role != 'editor' and project.owner != request.user:
        raise PermissionDenied("У вас нет прав на удаление этой задачи.")

    if request.method == 'POST':
        task.delete()
        return redirect('task-list')
    return render(request, 'task_confirm_delete.html', {'task': task})

#notifications
@login_required
def notifications(request):
    invitations = ProjectInvitation.objects.filter(invited_user=request.user, is_accepted=False)
    task_notifications = TaskAssignmentNotification.objects.filter(user=request.user)
    return render(request, 'notifications.html', {
        'invitations': invitations,
        'task_notifications': task_notifications,
    })

@login_required
def delete_task_notification(request, notification_id):
    notification = get_object_or_404(TaskAssignmentNotification, id=notification_id, user=request.user)
    notification.delete()
    return redirect('notifications')

#sent invite view
@login_required
def send_invitation(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    search_query = request.GET.get("search_user", "")
    selected_user = None
    error_message = ""

    if search_query:
        selected_user = User.objects.filter(username=search_query).first()
        if not selected_user:
            error_message = "Пользователь не найден"

    if request.method == 'POST':
        selected_username = request.POST.get("selected_user")
        invited_user = User.objects.filter(username=selected_username).first()

        if invited_user == request.user:
            self_invitation_error = True
            return render(request, 'send_invitation.html', {
                'project': project,
                'search_query': search_query,
                'selected_user': selected_user,
                'self_invitation_error': self_invitation_error,
            })

        if invited_user:
            form = ProjectInvitationForm(request.POST)
            if form.is_valid():
                invitation = form.save(commit=False)
                invitation.project = project
                invitation.inviter = request.user
                invitation.invited_user = invited_user
                invitation.save()

                success_message = f"Приглашение отправлено пользователю {invited_user.username}."
                return render(request, 'send_invitation.html', {
                    'project': project,
                    'search_query': search_query,
                    'selected_user': selected_user,
                    'success_message': success_message,
                })
            else:
                error_message = "Ошибка при отправке приглашения."

    return render(request, 'send_invitation.html', {
        'form': ProjectInvitationForm(),
        'project': project,
        'search_query': search_query,
        'selected_user': selected_user,
        'error_message': error_message,
    })

@login_required
def accept_invitation(request, invitation_id):
    invitation = get_object_or_404(ProjectInvitation, id=invitation_id, invited_user=request.user)
    
    if not invitation.is_accepted:
        invitation.accept_invitation()
    
    return redirect('notifications')

@login_required
def reject_invitation(request, invitation_id):
    invitation = get_object_or_404(ProjectInvitation, id=invitation_id, invited_user=request.user)
    
    if not invitation.is_accepted:
        invitation.is_accepted = True
        invitation.save()

    return redirect('notifications')

@login_required
def manage_participant(request, project_id, user_id):
    project = get_object_or_404(Project, pk=project_id)

    if project.owner != request.user:
        raise PermissionDenied("У вас нет прав на управление участниками этого проекта.")

    participant = get_object_or_404(ProjectMembership, project=project, user__id=user_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        new_role = request.POST.get('new_role')

        if action == 'change_role':
            participant.role = new_role
            participant.save()
        
        elif action == 'remove':

            Task.objects.filter(project=project, owner=participant.user).update(owner=project.owner)
            Task.objects.filter(project=project, assigned_to=participant.user).update(assigned_to=project.owner)

            participant.delete()

        return redirect('project-participants', pk=project_id)

    return redirect('project-participants', pk=project_id)
