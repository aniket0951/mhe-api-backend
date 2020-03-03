from apps.patients.models import Patient, FamilyMember 
from rest_framework import permissions


class Is_ManipalUser(permissions.BasePermission):
    """
    Is External User
    """
    message = 'Only Manipal App Users has the permission to access this.'

    def has_permission(self, request, view):
        return Patient.objects.filter(user_ptr_id=request.user.id).exists()


class IsLegitUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user.id
        if request.method == "POST":
            patient_id = request.data.get("user_id")
        if request.method == "GET":
            patient_id = request.query_params.get("user_id")
        if (patient_id is None) or (str(user) == patient_id):
            return True
        else:
            return FamilyMember.objects.filter(patient_info=user,id=patient_id).exists()
