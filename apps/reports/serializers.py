import logging
from apps.doctors.serializers import DoctorSerializer
from apps.master_data.serializers import HospitalSerializer
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url, patient_user_object

from .models import (ReportFile, FreeTextReportDetails, NumericReportDetails, Report,
                     ReportDocuments, StringReportDetails, TextReportDetails,
                     VisitReport)

logger = logging.getLogger("django")

class NumericReportDetailsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = NumericReportDetails
        exclude = ('created_at', 'updated_at',)


class FreeTextReportDetailsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FreeTextReportDetails
        exclude = ('created_at', 'updated_at',)


class StringReportDetailsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = StringReportDetails
        exclude = ('created_at', 'updated_at',)


class TextReportDetailsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TextReportDetails
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['observation_value'] = instance.observation_value.replace(
            'nbsp;', '')
        return data


class ReportSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Report
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if not self.context.get('request', None):
            response_object['text_reports'] = TextReportDetailsSerializer(
                instance.text_report.all(),
                many=True).data
            response_object['string_reports'] = StringReportDetailsSerializer(
                instance.string_report.all(),
                many=True).data
            response_object['numeric_reports'] = NumericReportDetailsSerializer(
                instance.numeric_report.all(),
                many=True).data
            response_object['free_text_reports'] = FreeTextReportDetailsSerializer(
                instance.free_text_report.all(),
                many=True).data

            if instance.doctor:
                response_object['doctor'] = DoctorSerializer(
                    instance.doctor).data

            if instance.hospital:
                response_object['hospital'] = HospitalSerializer(
                    instance.hospital).data

            return response_object

        if not self.context['request'].query_params.get('numeric_report__identifier', None):

            response_object['text_reports'] = TextReportDetailsSerializer(
                instance.text_report.all(),
                many=True).data
            response_object['string_reports'] = StringReportDetailsSerializer(
                instance.string_report.all(),
                many=True).data
            response_object['numeric_reports'] = NumericReportDetailsSerializer(
                instance.numeric_report.all(),
                many=True).data
            response_object['free_text_reports'] = FreeTextReportDetailsSerializer(
                instance.free_text_report.all(),
                many=True).data
        else:
            response_object['numeric_reports'] = NumericReportDetailsSerializer(
                instance.numeric_report.all().filter(
                    identifier=self.context['request'].query_params.get('numeric_report__identifier')),
                many=True).data

        if instance.doctor:
            response_object['doctor'] = DoctorSerializer(
                instance.doctor).data

        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(
                instance.hospital).data

        response_object['patient_class'] = instance.get_patient_class_display()
        response_object['family_member'] = None

        patient_user = patient_user_object(self.context['request'])
        if patient_user:
            response_object['patient'] = PatientSerializer(
                patient_user,
                fields=('id', 'mobile', 'uhid_number', 'first_name', 'display_picture',
                        'email', 'gender', 'last_name')).data

        family_member_id = self.context['request'].query_params.get(
            'user_id', None)

        if family_member_id:
            family_member = FamilyMember.objects.filter(patient_info=patient_user,
                                                        id=family_member_id).first()
            response_object['family_member'] = FamilyMemberSerializer(
                family_member,
                fields=('id', 'mobile', 'relation_name', 'uhid_number', 'display_picture', 'gender',
                        'first_name', 'last_name')).data

        return response_object


class ReportDocumentsSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = ReportDocuments
        fields = '__all__'
        extra_kwargs = {
            'name': {"error_messages": {"required": "Name is mandatory to upload your document."}},
        }

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        try:
            if instance.lab_report:
                response_object['lab_report'] = generate_pre_signed_url(
                    instance.lab_report.url)

            if instance.radiology_report:
                response_object['radiology_report'] = generate_pre_signed_url(
                    instance.radiology_report.url)

        except Exception as error:
            logger.error("Error while ReportDocumentsSerializer : %s"%str(error))
            response_object['lab_report'] = None
            response_object['radiology_report'] = None

        return response_object


class VisitReportsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = VisitReport
        exclude = ()

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        response_object["patient_type"] = None
        
        if instance.visit_id:
            radiology = self.context['request'].query_params.get(
                "radiology", None)
            reports = Report.objects.filter(
                visit_id=instance.visit_id, report_type="Lab").distinct("place_order", "code")
            if radiology:
                reports = Report.objects.filter(
                    visit_id=instance.visit_id, report_type="Radiology").distinct("place_order", "code")
            if reports:
                response_object["reports"] = ReportSerializer(
                    reports, many=True).data
            response_object["report_result"] = None
            document = ReportDocuments.objects.filter(
                episode_number=instance.visit_id).first()
            if document:
                response_object["report_result"] = ReportDocumentsSerializer(
                    document).data

            report = Report.objects.filter(visit_id=instance.visit_id).first()
            if report:
                response_object["patient_type"] = report.patient_class

        return response_object
    
class ReportFileSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = ReportFile
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        try:
            if instance.report_file:
                response_object['report_file'] = generate_pre_signed_url(
                    instance.report_file.url)

        except Exception as error:
            logger.error("Error while DownloadReportSerializer : %s"%str(error))
            response_object['report_file'] = None

        return response_object
