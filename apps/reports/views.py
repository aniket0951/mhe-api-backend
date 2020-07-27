from datetime import date, datetime, timedelta

from django.db.models import Q

from apps.patients.models import FamilyMember
from apps.master_data.models import Hospital
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

from .filters import ReportFilter
from .models import (FreeTextReportDetails, NumericReportDetails, Report,
                     ReportDocuments, StringReportDetails, TextReportDetails)
from .serializers import (FreeTextReportDetailsSerializer,
                          NumericReportDetailsSerializer,
                          ReportDocumentsSerializer, ReportSerializer,
                          StringReportDetailsSerializer,
                          TextReportDetailsSerializer)
from .utils import (free_text_report_hanlder, numeric_report_hanlder,
                    report_handler, string_report_hanlder, text_report_hanlder)


class ReportViewSet(custom_viewsets.ListCreateViewSet):
    permission_classes = [AllowAny]
    model = Report
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    create_success_message = "New report is added successfully."
    list_success_message = 'Report list returned successfully!'
    filter_backends = (DjangoFilterBackend,)
    filter_class = ReportFilter

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
        filter_by = self.request.query_params.get("filter_by", None)
        request_patient_obj = patient_user_object(self.request)

        qs = Report.objects.none()

        if family_member_id:
            family_member = FamilyMember.objects.filter(patient_info=request_patient_obj,
                                                        id=family_member_id).first()
            if not family_member:
                raise ValidationError("Family member not found!")

            if not family_member.uhid_number:
                raise ValidationError(
                    "UHID is not linked to your family member!")

            qs = Report.objects.filter(
                uhid=family_member.uhid_number).distinct()
        else:
            if not request_patient_obj.uhid_number:
                raise ValidationError("Your UHID is not linked!")

            qs = Report.objects.filter(
                uhid=request_patient_obj.uhid_number).distinct()

        if filter_by:
            if filter_by == "current_week":
                current_week = date.today().isocalendar()[1]
                current_year = date.today().isocalendar()[0]
                return qs.filter(time__week=current_week, time__year=current_year)
            elif filter_by == "last_week":
                previous_week = date.today() - timedelta(weeks=1)
                last_week = previous_week.isocalendar()[1]
                current_year = previous_week.isocalendar()[0]
                return qs.filter(time__week=last_week, time__year=current_year)
            elif filter_by == "last_month":
                last_month = datetime.today().replace(day=1) - timedelta(days=1)
                return qs.filter(time__month=last_month.month, time__year=last_month.year)
            elif filter_by == "current_month":
                current_month = datetime.today()
                return qs.filter(time__month=current_month.month, time__year=current_month.year)
            elif filter_by == "date_range":
                date_from = self.request.query_params.get("date_from", None)
                date_to = self.request.query_params.get("date_to", None)
                return qs.filter(time__date__range=[date_from, date_to])
            else:
                return qs.filter(time__date=filter_by)

        return qs


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


class FreeTextReportDetailsViewSet(custom_viewsets.CreateViewSet):
    permission_classes = [InternalAPICall]
    model = FreeTextReportDetails
    queryset = FreeTextReportDetails.objects.all()
    serializer_class = FreeTextReportDetailsSerializer
    create_success_message = "New free text report is added successfully."


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
        try:
            report_response = ReportViewSet.as_view(
                {'post': 'create'})(proxy_request)
        except:
            return Response({"data": report_response.data, "consumed": False},
                            status=status.HTTP_200_OK)

        if report_response.status_code == 201 and report_details and\
                type(report_details) == list:

            for each_report_detail in report_details:
                if each_report_detail['ObxType'] == 'NM':
                    numeric_report_proxy_request = numeric_report_hanlder(report_detail=each_report_detail,
                                                                          report_id=report_response.data['data']['id'])
                    NumericReportDetailsViewSet.as_view(
                        {'post': 'create'})(numeric_report_proxy_request)
                    continue

                if each_report_detail['ObxType'] == 'ST':
                    string_report_proxy_request = string_report_hanlder(report_detail=each_report_detail,
                                                                        report_id=report_response.data['data']['id'])
                    StringReportDetailsViewSet.as_view(
                        {'post': 'create'})(string_report_proxy_request)
                    continue

                if each_report_detail['ObxType'] == 'TX':
                    text_report_proxy_request = text_report_hanlder(report_detail=each_report_detail,
                                                                    report_id=report_response.data['data']['id'])
                    TextReportDetailsViewSet.as_view(
                        {'post': 'create'})(text_report_proxy_request)
                    continue

                if each_report_detail['ObxType'] == 'FT':
                    string_report_proxy_request = free_text_report_hanlder(report_detail=each_report_detail,
                                                                           report_id=report_response.data['data']['id'])
                    FreeTextReportDetailsViewSet.as_view(
                        {'post': 'create'})(string_report_proxy_request)

            return Response({"data": None, "consumed": True},
                            status=status.HTTP_201_CREATED)

        return Response({"data": report_response.data, "consumed": False},
                        status=status.HTTP_200_OK)


class PrescriptionDocumentsViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    model = ReportDocuments
    queryset = ReportDocuments.objects.all().order_by('-created_at')
    serializer_class = ReportDocumentsSerializer
    create_success_message = "Report Document is uploaded successfully."
    list_success_message = 'Report Documents returned successfully!'
    retrieve_success_message = 'Report Documents information returned successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, )

    def get_queryset(self):
        queryset = super().get_queryset()
        uhid = self.request.query_params.get("uhid", None)
        if not uhid:
            raise ValidationError("Invalid Parameters")
        return queryset.filter(uhid=uhid)

    def create(self, request):
        document_param = dict()
        file_type = request.data.get("file_type")
        episode_number = request.data.get("episode_number")
        for i, f in enumerate(request.FILES.getlist('reports')):
            hospital_code = request.data.get("hospital_code")
            hospital = Hospital.objects.filter(code=hospital_code).first()
            if not hospital:
                raise ValidationError("Hospital Not Available")
            document_param["file_type"] = file_type
            if file_type == "Radiology":
                document_param["radiology_report"] = f
                document_param["radiology_name"] = f.name
            else:
                document_param["lab_report"] = f
                document_param["lab_name"] = f.name
            document_param["uhid"] = request.data.get("uhid")
            document_param["episode_number"] = episode_number
            document_param["hospital"] = hospital.id
            document_serializer = self.serializer_class(data=document_param)
            report_instance = ReportDocuments.objects.filter(episode_number=episode_number).first()
            if report_instance:
                document_serializer = self.serializer_class(
                    report_instance, data=document_param, partial=True)
            document_serializer.is_valid(raise_exception=True)
            document_serializer.save()

        return Response(data={"message": "File Upload Sucessful"}, status=status.HTTP_200_OK)
