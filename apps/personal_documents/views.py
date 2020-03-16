from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import AllowAny, IsAuthenticated

from utils import custom_viewsets
from utils.custom_permissions import (BlacklistDestroyMethodPermission,
                                      BlacklistUpdateMethodPermission,
                                      IsManipalAdminUser, IsPatientUser,
                                      IsSelfDocument)

from .models import PatientPersonalDocuments
from .serializers import PatientPersonalDocumentsSerializer


class PatientPersonalDocumentsViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = PatientPersonalDocuments
    queryset = PatientPersonalDocuments.objects.all()
    serializer_class = PatientPersonalDocumentsSerializer
    create_success_message = "New personal document is uploaded successfully."
    list_success_message = 'Documents returned successfully!'
    retrieve_success_message = 'Document information returned successfully!'
    update_success_message = 'Document information is updated successfuly!'
    delete_success_message = 'Your document is deleted successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['name', 'description']
    ordering_fields = ('name', 'updated_at', 'created_at')

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
        return super().get_queryset().filter(patient_info_id=self.request.user.id)
