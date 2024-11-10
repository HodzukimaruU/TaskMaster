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
        label="Project name",
        widget=forms.TextInput(attrs={'placeholder': 'Enter project name'}),
    )
    description = forms.CharField(
        max_length=500,
        required=False,
        label="Project description",
        widget=forms.Textarea(attrs={'placeholder': 'Enter a description', 'class': 'no-resize'}),
    )

    class Meta:
        model = Project
        fields = ['title', 'description']

class TaskForm(forms.ModelForm):
    title = forms.CharField(
        max_length=100,
        label="Task name",
        widget=forms.TextInput(attrs={'placeholder': 'Enter a task name'}),
    )
    description = forms.CharField(
        required=False,
        label="Description of the task",
        widget=forms.Textarea(attrs={'placeholder': 'Enter a description', 'class': 'no-resize'}),
    )
    due_date = forms.DateTimeField(
        label="Due date",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )
    priority = forms.ChoiceField(
        choices=Task.PRIORITY_CHOICES,
        label="Priority",
    )
    status = forms.ChoiceField(
        choices=Task.STATUS_CHOICES,
        label="Status",
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        label="Project",
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Responsible",
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'status', 'project', 'assigned_to']

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        hide_assigned = kwargs.pop('hide_assigned', False)
        super(TaskForm, self).__init__(*args, **kwargs)
        
        if hide_assigned:
            self.fields.pop('assigned_to')
            self.fields.pop('project')
        elif project:
            self.fields['assigned_to'].queryset = project.members.all()

    def save(self, commit=True, user=None):
        task = super().save(commit=False)
        if not task.project and not task.assigned_to:
            task.assigned_to = user
        if commit:
            task.save()
        return task

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
