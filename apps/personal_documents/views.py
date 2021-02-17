from django.db.models import Q
from django.conf import settings
from rest_framework import filters
from ratelimit.decorators import ratelimit
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from apps.patients.exceptions import InvalidFamilyMemberValidationException
from apps.patients.models import FamilyMember
from utils import custom_viewsets
from utils.custom_permissions import (
                                BlacklistUpdateMethodPermission,
                                IsPatientUser,
                                IsSelfDocument
                            )
from .models import PatientPersonalDocuments
from .serializers import PatientPersonalDocumentsSerializer

@method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_DOCUMENT_UPLOAD, block=True, method=ratelimit.UNSAFE), name='create')
class PatientPersonalDocumentsViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = PatientPersonalDocuments
    queryset = PatientPersonalDocuments.objects.all().order_by('-created_at')
    serializer_class = PatientPersonalDocumentsSerializer
    create_success_message = "New personal document is uploaded successfully."
    list_success_message = 'Documents returned successfully!'
    retrieve_success_message = 'Document information returned successfully!'
    update_success_message = 'Document information is updated successfuly!'
    delete_success_message = 'Your document is deleted successfuly!'
    filter_backends = (DjangoFilterBackend,filters.SearchFilter, )
    search_fields = ['name', 'description']

    def get_permissions(self):
        if self.action in ['list', 'create', ]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'retrieve', 'destroy']:
            permission_classes = [IsPatientUser, IsSelfDocument]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        family_member = self.request.query_params.get("user_id", None)
        if family_member is not None:
            family_member_obj = FamilyMember.objects.filter(id=family_member,
                                                            patient_info_id=self.request.user.id).first()
            if not family_member_obj:
                raise InvalidFamilyMemberValidationException
            return super().get_queryset().filter((Q(patient_info_id=self.request.user.id) & Q(family_member_id=family_member)))
        else:
            return super().get_queryset().filter((Q(patient_info_id=self.request.user.id) & Q(family_member__isnull=True)))
