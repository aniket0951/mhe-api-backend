from apps.doctors.serializers import DoctorSerializer
from apps.master_data.serializers import HospitalSerializer
from apps.patients.models import FamilyMember
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import patient_user_object

from .models import (NumericReportDetails, Report, StringReportDetails,
                     TextReportDetails, FreeTextReportDetails)


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
        if not self.context['request'].query_params.get('numeric_report__identifier', None):

            if self.context['request'].query_params.get('text_report__isnull') and\
                    self.context['request'].query_params.get('text_report__isnull') == 'False':

                response_object['text_reports'] = TextReportDetailsSerializer(
                    instance.text_report.all(),
                    many=True).data
            else:
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
