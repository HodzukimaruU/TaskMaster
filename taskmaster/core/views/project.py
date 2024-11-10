from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden

from core.models import Project, ProjectMembership, ProjectChatMessage
from core.forms import ProjectForm
from core.utils import get_user_role_in_project

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

@login_required
def project_detail(request, pk):
    project = Project.objects.filter(
        Q(pk=pk) & (Q(owner=request.user) | Q(members=request.user))
    ).distinct().first()
    
    if not project:
        return HttpResponseForbidden("Project not found or you do not have access.")

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
        return HttpResponseForbidden("You do not have access to this project.")

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
        return HttpResponseForbidden("You do not have access to this project's chat.")

    messages = ProjectChatMessage.objects.filter(project=project).order_by('created_at')

    if request.method == "POST":
        message_text = request.POST.get("message")
        if message_text:
            ProjectChatMessage.objects.create(project=project, user=request.user, message=message_text)
    
    return render(request, 'project_chat.html', {
        'project': project,
        'messages': messages
    })
