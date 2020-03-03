from rest_framework import permissions

from apps.manipal_admin.models import ManipalAdmin
from apps.patients.models import Patient


class IsManipalAdminUser(permissions.BasePermission):
    """
    Is Manipal Admin User
    """
    message = 'You do not have permission to access this information.'

    def has_permission(self, request, view):
        """
        Checking if the user is Manipal administartor.
        """
        try:
            if ManipalAdmin.objects.filter(id=request.user.id).exists():
                return True
        except Exception as e:
            print(e)
            pass
        self.message = 'Manipal Administrator has the permission to perform this action.'
        return False


class IsPatientUser(permissions.BasePermission):
    """
    Is Patient User
    """
    message = 'You do not have permission to access this information.'

    def has_permission(self, request, view):
        """
        Checking if the user is Patient.
        """
        try:
            if hasattr(request.user, 'mobile'):
                if Patient.objects.filter(mobile=request.user.mobile).exists():
                    return True
        except Exception as e:
            print(e)
            pass
        self.message = 'Patient has the permission to perform this action.'
        return False


class SelfUserAccess(permissions.BasePermission):
    message = 'You do not have permission to access this object.'

    def has_object_permission(self, request, view, obj):
        return request.user.id == obj.id


class BlacklistUpdateMethodPermission(permissions.BasePermission):
    """
    Global permission check for blacklisted UPDATE method.
    """
    message = 'You do not have permission to do this action.'

    def has_permission(self, request, view):
        return request.method != 'PUT'

    def has_object_permission(self, request, view, obj):
        return request.method != 'PUT'


class BlacklistDestroyMethodPermission(permissions.BasePermission):
    """
    Global permission check for blacklisted UPDATE method.
    """
    message = 'You do not have permission to do this action.'

    def has_permission(self, request, view):
        return request.method != 'DELETE'

    def has_object_permission(self, request, view, obj):
        return request.method != 'DELETE'
