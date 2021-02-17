import logging
from rest_framework import permissions

from apps.manipal_admin.models import ManipalAdmin
from apps.patients.models import FamilyMember, Patient

DO_NOT_HAVE_PERMISSION = "You do not have permission to do this action."

logger = logging.getLogger("django")

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
            logger.error("Error while IsManipalAdminUser : %s"%str(e))
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
            if hasattr(request.user, 'mobile') and Patient.objects.filter(mobile=request.user.mobile).exists():
                return True
        except Exception:
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
    message = DO_NOT_HAVE_PERMISSION

    def has_permission(self, request, view):
        return request.method != 'PUT'

    def has_object_permission(self, request, view, obj):
        return request.method != 'PUT'


class BlacklistDestroyMethodPermission(permissions.BasePermission):
    """
    Global permission check for blacklisted UPDATE method.
    """
    message = DO_NOT_HAVE_PERMISSION

    def has_permission(self, request, view):
        return request.method != 'DELETE'

    def has_object_permission(self, request, view, obj):
        return request.method != 'DELETE'


class IsSelfUserOrFamilyMember(permissions.BasePermission):

    message = DO_NOT_HAVE_PERMISSION

    def has_permission(self, request, view):
        patient_id = None
        user = request.user.id
        if request.method == "POST":
            patient_id = request.data.get("user_id", None)
        if request.method == "GET":
            patient_id = request.query_params.get("user_id", None)
        if (patient_id is None) or (str(user) == patient_id):
            return True
        else:
            return FamilyMember.objects.filter(patient_info=user, id=patient_id).exists()


class IsSelfFamilyMember(permissions.BasePermission):

    message = DO_NOT_HAVE_PERMISSION

    def has_object_permission(self, request, view, obj):
        return request.user.id == obj.patient_info.id


class IsSelfAddress(permissions.BasePermission):

    message = DO_NOT_HAVE_PERMISSION

    def has_object_permission(self, request, view, obj):
        return request.user.id == obj.patient_info.id


class IsSelfDocument(permissions.BasePermission):

    message = DO_NOT_HAVE_PERMISSION

    def has_object_permission(self, request, view, obj):
        return request.user.id == obj.patient_info.id


class IsSelfHealthPackageCartItem(permissions.BasePermission):

    message = DO_NOT_HAVE_PERMISSION

    def has_object_permission(self, request, view, obj):
        return request.user.id == obj.patient_info.id


class IsSelfHomeCollectionCartItem(permissions.BasePermission):

    message = DO_NOT_HAVE_PERMISSION

    def has_object_permission(self, request, view, obj):
        return request.user.id == obj.patient_info.id

class InternalAPICall(permissions.BasePermission):

    message = DO_NOT_HAVE_PERMISSION

    def has_permission(self, request, view):
        return request.get_host() == 'testserver'

class IsDoctor(permissions.BasePermission):

    message = DO_NOT_HAVE_PERMISSION

    def has_object_permission(self, request, view, obj):
        doctor_id = request.user.id
        return Doctor.objects.filter(id = doctor_id).exists()

class IsPlatformAdmin(permissions.BasePermission):

    message = 'You do not have permission to do this action.'

    def has_permission(self, request, view):
        """
        Checking if the user is Manipal administartor.
        """
        try:
            if ManipalAdmin.objects.filter(id=request.user.id, role__name__contains = 'Platform Admin').exists():
                return True
        except Exception as e:
            pass
        self.message = 'Manipal Administrator has the permission to perform this action.'
        return False

        
