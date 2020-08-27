from datetime import date, datetime, timedelta

from django.db.models import Q

from apps.master_data.models import Hospital
from apps.patients.models import FamilyMember
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory
from utils import custom_viewsets
from utils.custom_permissions import InternalAPICall, IsPatientUser
from utils.utils import patient_user_object

from .models import DischargeSummary
from .serializers import DischargeSummarysSerializer


class DischargeViewSet(custom_viewsets.ListCreateViewSet):
    permission_classes = [AllowAny, ]
    model = DischargeSummary
    queryset = DischargeSummary.objects.all()
    serializer_class = DischargeSummarysSerializer
    create_success_message = "Discharge Summary is added successfully."
    list_success_message = 'Discharge Summaries returned successfully!'
    filter_backends = (DjangoFilterBackend,)

    def get_permissions(self):
        if self.action in ['list', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['create']:
            permission_classes = [InternalAPICall]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        uhid = self.request.query_params.get('uhid', None)
        if not uhid:
            raise ValidationError("Parameter Missing")
        return qs.filter(uhid=uhid)


class DischargeSummarySyncAPIView(CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        discharge_info = request.data.get('MDMMessage', None)
        discharge_details = request.data.get('MDMDetails', None)
        import pdb; pdb.set_trace()
        proxy_request = report_handler(report_info=report_info)

        if not proxy_request:
            ValidationError("Something went wrong!")
        try:
            report_response = ReportViewSet.as_view(
                {'post': 'create'})(proxy_request)
        except:
            return Response({"data": report_response.data, "consumed": False},
                            status=status.HTTP_200_OK)

            return Response({"data": None, "consumed": True},
                            status=status.HTTP_201_CREATED)

        return Response({"data": report_response.data, "consumed": False},
                        status=status.HTTP_200_OK)