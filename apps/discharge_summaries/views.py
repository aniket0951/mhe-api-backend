from datetime import date, datetime, timedelta
import os 
import logging
from django.db.models import Q

from apps.master_data.models import Hospital
from apps.patients.models import FamilyMember
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser,FileUploadParser
from rest_framework import filters, generics, status, viewsets
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory
from utils import custom_viewsets
from utils.custom_permissions import InternalAPICall, IsPatientUser
from utils.pdf_generator import get_discharge_summary
from utils.utils import patient_user_object

from .models import DischargeSummary
from .serializers import DischargeSummarysSerializer
from apps.doctors.models import Doctor
from apps.master_data.models import Department, Hospital

logger = logging.getLogger('django')

class DischargeViewSet(custom_viewsets.ListCreateViewSet):
    permission_classes = [AllowAny, ]
    model = DischargeSummary
    queryset = DischargeSummary.objects.all()
    parser_classes = (MultiPartParser, FormParser)
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

    def create(self, request):
        try:
            data = request.data
            visit_id = data["visit_id"]
            discharge_obj = DischargeSummary.objects.filter(visit_id=visit_id).first()
            doctor_code = data.pop("doctor_code")
            if doctor_code:
                doctor = Doctor.objects.filter(code=doctor_code)
                if doctor:
                    data["doctor"] = doctor.id
            data["time"] = datetime.strptime(
                data["time"], '%Y%m%d%H%M%S') 
            serializer = DischargeSummarysSerializer(data=data)
            if discharge_obj:
                serializer = DischargeSummarysSerializer(discharge_obj, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"message": "File Upload Sucessful"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Exception in DischargeViewSet: %s"%(str(e)))
            return Response(data={"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DischargeSummarySyncAPIView(CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            discharge_info = request.data.get('MDMMessage', None)
            discharge_details = request.data.get('MDMDetails', None)
            file_name = get_discharge_summary(discharge_info, discharge_details)
            os.remove(file_name)
        except Exception as e:
            return Response(data={"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": None, "consumed": True},status=status.HTTP_201_CREATED)
