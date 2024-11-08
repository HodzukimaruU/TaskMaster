from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    index, register_view, login_view, logout_view,
    confirm_email, confirm_email_stub_controller,
    project_list, project_create, project_detail, project_update, project_delete, project_participants,
    task_list, task_create, task_update, task_delete, task_detail,
    send_invitation, accept_invitation, notifications
    )

urlpatterns = [
    path('', index, name='index'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('confirm-email/', confirm_email, name='confirm_email'),
    path('confirm-email-sent/', confirm_email_stub_controller, name='confirm_email_sent'),

    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('projects/', project_list, name='project-list'),
    path('projects/new/', project_create, name='project-create'),
    path('projects/<int:pk>/', project_detail, name='project-detail'),
    path('projects/<int:pk>/edit/', project_update, name='project-update'),
    path('projects/<int:pk>/delete/', project_delete, name='project-delete'),

    path('tasks/', task_list, name='task-list'),
    path('tasks/new/', task_create, name='task-create'),
    path('tasks/<int:pk>/edit/', task_update, name='task-update'),
    path('tasks/<int:pk>/', task_detail, name='task-detail'),
    path('tasks/<int:pk>/delete/', task_delete, name='task-delete'),

    path('projects/<int:project_id>/invite/', send_invitation, name='send_invitation'),
    path('projects/<int:pk>/participants/', project_participants, name='project-participants'),

    path('invitations/accept/<int:invitation_id>/', accept_invitation, name='accept_invitation'),
    path('notifications/', notifications, name='notifications'),

]
