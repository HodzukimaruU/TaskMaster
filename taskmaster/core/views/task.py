from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.http import HttpRequest, HttpResponse

from core.models import Project, Task, TaskAssignmentNotification
from core.forms import TaskForm
from core.utils import get_user_role_in_project


@login_required
def task_list(request: HttpRequest) -> HttpResponse:
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
def task_create(request: HttpRequest) -> HttpResponse:
    project = None
    if 'project' in request.GET:
        project_id = request.GET['project']
        project = get_object_or_404(Project, id=project_id)

    if project:
        role = get_user_role_in_project(request.user, project)
        if role != 'editor' and request.user != project.owner:
            return HttpResponseForbidden("You do not have permission to add issues to this project.")

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
def task_update(request: HttpRequest, pk: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=pk)
    hide_assigned = task.project is None
    project = task.project

    if project:
        role = get_user_role_in_project(request.user, project)
        if role not in ['viewer', 'editor'] and request.user != project.owner:
            return HttpResponseForbidden("You do not have permission to edit this issue.")
    else:
        if request.user != task.owner:
            return HttpResponseForbidden("You do not have permission to edit this issue.")

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
def task_detail(request: HttpRequest, pk: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=pk)

    role = None

    if task.project:
        role = get_user_role_in_project(request.user, task.project)
        if role not in ['viewer', 'editor'] and request.user != task.project.owner:
            return HttpResponseForbidden("You don't have access to this task.")
    else:
        if request.user != task.owner and request.user != task.assigned_to:
            return HttpResponseForbidden("You don't have access to this task.")

    return render(request, 'task_detail.html', {'task': task, 'role': role})


@login_required
def task_delete(request: HttpRequest, pk: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    role = get_user_role_in_project(request.user, project)

    if request.user != task.assigned_to and role != 'editor' and project.owner != request.user:
        return HttpResponseForbidden("You do not have permission to delete this task.")

    if request.method == 'POST':
        task.delete()
        return redirect('task-list')
    return render(request, 'task_confirm_delete.html', {'task': task})
