from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from core.models import ProjectInvitation, TaskAssignmentNotification

@login_required
def notifications_view(request):
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
