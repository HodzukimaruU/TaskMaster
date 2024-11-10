from .models import ProjectMembership

def get_user_role_in_project(user, project):
    try:
        membership = ProjectMembership.objects.get(user=user, project=project)
        return membership.role
    except ProjectMembership.DoesNotExist:
        return None