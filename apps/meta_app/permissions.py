from rest_framework import permissions
from apps.users.models import BaseUser
from apps.manipal_admin.models import ManipalAdmin

class Is_ManipalUser(permissions.BasePermission):
    """
    Is External User
    """
    message = 'Only Manipal App Users has the permission to access this.'

    def has_permission(self, request, view):
        """
        Checking if the user is thinkAhoy user or not.
        """
        return BaseUser.objects.filter(user_ptr_id=request.user.id).exists()

class Is_ManipalAdmin(permissions.BasePermission):
    """
    Is External User
    """
    message = 'Only Manipal Admin Users has the permission to access this.'

    def has_permission(self, request, view):
        """
        Checking if the user is thinkAhoy user or not.
        """
        return ManipalAdmin.objects.filter(user_ptr_id=request.user.id).exists()



