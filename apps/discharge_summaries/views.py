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


class DischargeViewSet(custom_viewsets.ListCreateViewSet):
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