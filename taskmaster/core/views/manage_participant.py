from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden

from core.models import Project, Task,ProjectMembership

@login_required
def manage_participant_view(request, project_id, user_id):
    project = get_object_or_404(Project, pk=project_id)

    if project.owner != request.user:
        return HttpResponseForbidden("You do not have rights to manage members of this project.")

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
