from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory

from apps.patients.models import FamilyMember
from utils import custom_viewsets
from utils.custom_permissions import InternalAPICall, IsPatientUser
from utils.utils import patient_user_object

from .models import (NumericReportDetails, Report, StringReportDetails,
                     TextReportDetails)
from .serializers import (NumericReportDetailsSerializer, ReportSerializer,
                          StringReportDetailsSerializer,
                          TextReportDetailsSerializer)
from .utils import (numeric_report_hanlder, report_handler,
                    string_report_hanlder, text_report_hanlder)


class ReportViewSet(custom_viewsets.ListCreateViewSet):
    permission_classes = [AllowAny]
    model = Report
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    create_success_message = "New report is added successfully."
    list_success_message = 'Report list returned successfully!'
    filter_fields = ('numeric_report__identifier',)
    
    def get_permissions(self):
        if self.action in ['list', ]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['create']:
            permission_classes = [InternalAPICall]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        family_member_id = self.request.query_params.get('user_id', None)
        request_patient_obj = patient_user_object(self.request)
        if family_member_id:
            family_member = FamilyMember.objects.filter(patient_info=request_patient_obj,
                                                        id=family_member_id).first()
            if not family_member:
                raise ValidationError("Family member not found!")

            if family_member.uhid_number:
                return Report.objects.filter(uhid=family_member.uhid_number).distinct()

            raise ValidationError("UHID is not linked to your family member!")

        if request_patient_obj.uhid_number:
            return Report.objects.filter(uhid=request_patient_obj.uhid_number).distinct()

        raise ValidationError("Your UHID is not linked!")


class NumericReportDetailsViewSet(custom_viewsets.CreateViewSet):
    permission_classes = [InternalAPICall]
    model = NumericReportDetails
    queryset = NumericReportDetails.objects.all()
    serializer_class = NumericReportDetailsSerializer
    create_success_message = "New numeric report is added successfully."


class TextReportDetailsViewSet(custom_viewsets.CreateViewSet):
    permission_classes = [InternalAPICall]
    model = TextReportDetails
    queryset = TextReportDetails.objects.all()
    serializer_class = TextReportDetailsSerializer
    create_success_message = "New text report is added successfully."


class StringReportDetailsViewSet(custom_viewsets.CreateViewSet):
    permission_classes = [InternalAPICall]
    model = StringReportDetails
    queryset = StringReportDetails.objects.all()
    serializer_class = StringReportDetailsSerializer
    create_success_message = "New string report is added successfully."


class ReportsSyncAPIView(CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        report_info = request.data.get('ORUMessage', None)
        report_details = request.data.get('ORUDetails', None)
        proxy_request = report_handler(report_info=report_info)

        if not proxy_request:
            ValidationError("Something went wrong!")

        report_response = ReportViewSet.as_view(
            {'post': 'create'})(proxy_request)

        if report_response.status_code == 201 and report_details and\
                type(report_details) == list:

            for each_report_detail in report_details:
                if each_report_detail['ObxType'] == 'NM':
                    numeric_report_proxy_request = numeric_report_hanlder(report_detail=each_report_detail,
                                                                          report_id=report_response.data['data']['id'])
                    NumericReportDetailsViewSet.as_view(
                        {'post': 'create'})(numeric_report_proxy_request)
                if each_report_detail['ObxType'] == 'TX':
                    text_report_proxy_request = text_report_hanlder(report_detail=each_report_detail,
                                                                    report_id=report_response.data['data']['id'])
                    TextReportDetailsViewSet.as_view(
                        {'post': 'create'})(text_report_proxy_request)
                if each_report_detail['ObxType'] == 'ST':
                    string_report_proxy_request = string_report_hanlder(report_detail=each_report_detail,
                                                                        report_id=report_response.data['data']['id'])
                    StringReportDetailsViewSet.as_view(
                        {'post': 'create'})(string_report_proxy_request)

        return Response({"data": None}, status=status.HTTP_201_CREATED)
