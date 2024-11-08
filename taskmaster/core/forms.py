from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Project, Task, ProjectInvitation

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = ''

class ProjectForm(forms.ModelForm):
    title = forms.CharField(
        max_length=100,
        label="Название проекта",
        widget=forms.TextInput(attrs={'placeholder': 'Введите название проекта'}),
    )
    description = forms.CharField(
        max_length=500,
        required=False,
        label="Описание проекта",
        widget=forms.Textarea(attrs={'placeholder': 'Введите описание'}),
    )

    class Meta:
        model = Project
        fields = ['title', 'description']

class TaskForm(forms.ModelForm):
    title = forms.CharField(
        max_length=100,
        label="Название задачи",
        widget=forms.TextInput(attrs={'placeholder': 'Введите название задачи'}),
    )
    description = forms.CharField(
        required=False,
        label="Описание задачи",
        widget=forms.Textarea(attrs={'placeholder': 'Введите описание'}),
    )
    due_date = forms.DateTimeField(
        label="Срок выполнения",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )
    priority = forms.ChoiceField(
        choices=Task.PRIORITY_CHOICES,
        label="Приоритет",
    )
    status = forms.ChoiceField(
        choices=Task.STATUS_CHOICES,
        label="Статус",
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        label="Проект",
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'status', 'project']

class ProjectInvitationForm(forms.ModelForm):
    class Meta:
        model = ProjectInvitation
        fields = ['role']
        widgets = {
            'role': forms.Select(choices=[('viewer', 'Viewer'), ('editor', 'Editor')])
        }
        labels = {
            'role': 'Role in the Project'
        }
