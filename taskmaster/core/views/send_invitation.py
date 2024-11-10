from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse

from core.models import Project, ProjectInvitation
from core.forms import ProjectInvitationForm


@login_required
def send_invitation_view(request: HttpRequest, project_id: int) -> HttpResponse:
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    search_query = request.GET.get("search_user", "")
    selected_user = None
    error_message = ""

    if search_query:
        selected_user = User.objects.filter(username=search_query).first()
        if not selected_user:
            error_message = "User not found"

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

                success_message = f"An invitation has been sent to the user {invited_user.username}."
                return render(request, 'send_invitation.html', {
                    'project': project,
                    'search_query': search_query,
                    'selected_user': selected_user,
                    'success_message': success_message,
                })
            else:
                error_message = "Error sending invitation."

    return render(request, 'send_invitation.html', {
        'form': ProjectInvitationForm(),
        'project': project,
        'search_query': search_query,
        'selected_user': selected_user,
        'error_message': error_message,
    })


@login_required
def accept_invitation(request: HttpRequest, invitation_id: int) -> HttpResponse:
    invitation = get_object_or_404(ProjectInvitation, id=invitation_id, invited_user=request.user)
    
    if not invitation.is_accepted:
        invitation.accept_invitation()
    
    return redirect('notifications')


@login_required
def reject_invitation(request: HttpRequest, invitation_id: int) -> HttpResponse:
    invitation = get_object_or_404(ProjectInvitation, id=invitation_id, invited_user=request.user)
    
    if not invitation.is_accepted:
        invitation.is_accepted = True
        invitation.save()

    return redirect('notifications')
