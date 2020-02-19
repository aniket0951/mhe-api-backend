from apps.users.models import BaseUser, Relationship
from rest_framework import permissions


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


class Is_legit_user(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user.id
        print(request.method)
        if request.method == "POST":
            patient_id = request.data.get("user_id")
        if request.method == "GET":
            patient_id = request.query_params.get("user_id")
        print(user)
        print(patient_id)
        if str(user) == patient_id:
            return True
        else:
            return Relationship.objects.filter(relative_user_id=patient_id).exists()
