from datetime import date, datetime, timedelta
import xml.etree.ElementTree as ET
import logging

from django.db.models import Q

from apps.master_data.models import Hospital
from apps.patients.models import FamilyMember
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from utils import custom_viewsets
from utils.custom_permissions import BlacklistDestroyMethodPermission, BlacklistPartialUpdateMethodPermission, BlacklistUpdateMethodPermission, InternalAPICall, IsManipalAdminUser, IsPatientUser
from utils.utils import patient_user_object

from .filters import ReportFilter
from .models import (ReportFile, FreeTextReportDetails, NumericReportDetails, Report,
                     ReportDocuments, StringReportDetails, TextReportDetails,
                     VisitReport)
from .serializers import (ReportFileSerializer, FreeTextReportDetailsSerializer,
                          NumericReportDetailsSerializer,
                          ReportDocumentsSerializer, ReportSerializer,
                          StringReportDetailsSerializer,
                          TextReportDetailsSerializer, VisitReportsSerializer)
from .utils import ( create_visit_reports, free_text_report_hanlder, numeric_report_hanlder, report_handler, string_report_hanlder, text_report_hanlder, validate_family_member)

logger = logging.getLogger('django')


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

        if family_member_id:
            family_member = FamilyMember.objects.filter(patient_info=request_patient_obj,id=family_member_id).first()
            validate_family_member(family_member)
            qs = Report.objects.filter(uhid=family_member.uhid_number).distinct()

        else:
            if not request_patient_obj.uhid_number:
                raise ValidationError("Your UHID is not linked!")
            qs = Report.objects.filter(uhid=request_patient_obj.uhid_number).distinct()

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

        return qs.order_by('-time')


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


def process_reports_sync(report_details,report_response):

    for each_report_detail in report_details:
        
        if each_report_detail['ObxType'] == 'NM':
            numeric_report_proxy_request = numeric_report_hanlder(report_detail=each_report_detail,report_id=report_response.data['data']['id'])
            NumericReportDetailsViewSet.as_view({'post': 'create'})(numeric_report_proxy_request)
            continue

        if each_report_detail['ObxType'] == 'ST':
            string_report_proxy_request = string_report_hanlder(report_detail=each_report_detail,report_id=report_response.data['data']['id'])
            StringReportDetailsViewSet.as_view({'post': 'create'})(string_report_proxy_request)
            continue

        if each_report_detail['ObxType'] == 'TX':
            text_report_proxy_request = text_report_hanlder(report_detail=each_report_detail,report_id=report_response.data['data']['id'])
            TextReportDetailsViewSet.as_view({'post': 'create'})(text_report_proxy_request)
            continue

        if each_report_detail['ObxType'] == 'FT':
            string_report_proxy_request = free_text_report_hanlder(report_detail=each_report_detail,report_id=report_response.data['data']['id'])
            FreeTextReportDetailsViewSet.as_view({'post': 'create'})(string_report_proxy_request)

class ReportsSyncAPIView(CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            report_info = request.data.get('ORUMessage', None)
            root = ET.fromstring(report_info['msgORB'])
            report_info["place_order"] = root.find('OBR.2').find('OBR.2.1').text
            report_details = request.data.get('ORUDetails', None)
            proxy_request = report_handler(report_info=report_info)
            report_response = None
            if not proxy_request:
                ValidationError("Something went wrong!")
            try:
                report_response = ReportViewSet.as_view({'post': 'create'})(proxy_request)
            except Exception as error:
                logger.error("Exception in ReportsSyncAPIView %s"%(str(error)))
                return Response({"data": report_response.data if report_response else str(error), "consumed": False},status=status.HTTP_200_OK)
            
            report_info = create_visit_reports(report_response,report_info)

            if report_response.status_code == 201 and report_details and type(report_details) == list:
                
                process_reports_sync(report_details,report_response)

                return Response({"data": None, "consumed": True},status=status.HTTP_201_CREATED)

        except Exception as error:
            logger.error("Exception in ReportsSyncAPIView %s"%(str(error)))
            return Response({"data": "Parameters are not sufficient", "consumed": False},
                        status=status.HTTP_200_OK)

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
        file_type = request.query_params.get("file_type")
        episode_number = request.query_params.get("episode_number")
        for i, f in enumerate(request.FILES.getlist('reports')):
            hospital_code = request.query_params.get("hospital_code")
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
            document_param["uhid"] = request.query_params.get("uhid")
            document_param["episode_number"] = episode_number
            document_param["hospital"] = hospital.id
            document_serializer = self.serializer_class(data=document_param)
            report_instance = ReportDocuments.objects.filter(
                episode_number=episode_number).first()
            if report_instance:
                document_serializer = self.serializer_class(
                    report_instance, data=document_param, partial=True)
            document_serializer.is_valid(raise_exception=True)
            document_serializer.save()

        return Response(data={"message": "File Upload Sucessful"}, status=status.HTTP_200_OK)


class ReportVisitViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    model = VisitReport
    queryset = VisitReport.objects.all().order_by('-created_at')
    serializer_class = VisitReportsSerializer
    create_success_message = "Report is uploaded successfully."
    list_success_message = 'Report returned successfully!'
    retrieve_success_message = 'Report information returned successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, )

    def get_queryset(self):
        qs = super().get_queryset()
        uhid = self.request.query_params.get("uhid", None)
        filter_by = self.request.query_params.get("filter_by", None)
        patient_class = self.request.query_params.get("patient_class", None)
        radiology = self.request.query_params.get("radiology", None)

        if not uhid:
            raise ValidationError("Invalid Parameters")

        if radiology:
            qs = qs.filter(report_info__report_type="Radiology")

        else:
            qs = qs.filter(report_info__report_type="Lab")

        if filter_by:
            if filter_by == "current_week":
                current_week = date.today().isocalendar()[1]
                current_year = date.today().isocalendar()[0]
                qs = qs.filter(created_at__week=current_week,
                               created_at__year=current_year).distinct()
            elif filter_by == "last_week":
                previous_week = date.today() - timedelta(weeks=1)
                last_week = previous_week.isocalendar()[1]
                current_year = previous_week.isocalendar()[0]
                qs = qs.filter(created_at__week=last_week,
                               created_at__year=current_year).distinct()
            elif filter_by == "last_month":
                last_month = datetime.today().replace(day=1) - timedelta(days=1)
                qs = qs.filter(created_at__month=last_month.month,
                               created_at__year=last_month.year).distinct()
            elif filter_by == "current_month":
                current_month = datetime.today()
                qs = qs.filter(created_at__month=current_month.month,
                               created_at__year=current_month.year).distinct()
            elif filter_by == "date_range":
                date_from = self.request.query_params.get("date_from", None)
                date_to = self.request.query_params.get("date_to", None)
                qs = qs.filter(created_at__date__range=[
                               date_from, date_to]).distinct()
            else:
                qs = qs.filter(created_at__date=filter_by).distinct()

        if patient_class:
            qs = qs.filter(patient_class=patient_class).distinct()

        return qs.filter(uhid=uhid).order_by('-created_at').distinct()
    
    
class ReportFileViewSet(custom_viewsets.CreateUpdateListRetrieveModelViewSet):
    permission_classes = [AllowAny, ]
    model = ReportFile
    queryset = ReportFile.objects.all().order_by('-created_at')
    serializer_class = ReportFileSerializer
    create_success_message = "Report file is uploaded successfully."
    list_success_message = 'Report files returned successfully!'
    retrieve_success_message = 'Report file information returned successfully!'
    filter_backends = ( DjangoFilterBackend, filters.SearchFilter, )
    
    def get_permissions(self):

        if self.action in ['create']:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPatientUser | IsManipalAdminUser ]
            return [permission() for permission in permission_classes]
        
        if self.action == 'partial_update':
            permission_classes = [BlacklistPartialUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()
    
    def create(self, request):
        
        report_document_param = {
            "uhid"          : request.query_params.get("uhid"),
            "visit_id"      : request.query_params.get("visit_id"),
            "message_id"    : request.query_params.get("message_id")
        }
        
        for _, f in enumerate(request.FILES.getlist('report_file')):
            report_document_param["report_file"] = f

        report_instance = ReportFile.objects.filter(
                                        uhid=report_document_param["uhid"],
                                        visit_id=report_document_param["visit_id"]
                                    ).first()
        if report_instance:
            report_file_serializer = self.serializer_class(report_instance, data=report_document_param, partial=True)
        else:
            report_file_serializer = self.serializer_class(data=report_document_param)
            
        report_file_serializer.is_valid(raise_exception = True)
        report_object = report_file_serializer.save()
        
        data = {
                "data":self.serializer_class(report_object).data,
                "message": "Report file is Uploaded Successfully!"
            }
        return Response(data, status=status.HTTP_200_OK)
