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
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),  # Изначально пустой, будет заполнен позже
        required=False,
        label="Ответственный",
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'status', 'project', 'assigned_to']

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        hide_assigned = kwargs.pop('hide_assigned', False)
        super(TaskForm, self).__init__(*args, **kwargs)
        
        # Скрываем поле assigned_to, если hide_assigned=True
        if hide_assigned:
            self.fields.pop('assigned_to')
        elif project:
            self.fields['assigned_to'].queryset = project.members.all()

    def save(self, commit=True, user=None):
        task = super().save(commit=False)
        # Если задача создается без проекта и ответственный не выбран, назначаем текущего пользователя
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

class ProjectSearchForm(forms.Form):
    search_date = forms.DateField(
        widget=forms.SelectDateWidget(years=range(2020, 2031)), 
        required=False,
        label="Поиск по дате"
    )


class TaskSearchForm(forms.Form):
    search_date = forms.DateField(
        widget=forms.SelectDateWidget(years=range(2020, 2031)),
        required=False,
        label="Поиск задач по дате"
    )
