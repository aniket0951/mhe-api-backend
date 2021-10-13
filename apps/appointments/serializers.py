from apps.patients.models import Patient
import logging
from apps.doctors.serializers import (DoctorSerializer,
                                      HospitalSerializer)
from apps.health_packages.serializers import (HealthPackageSpecificSerializer)
from apps.master_data.models import Department
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url

from .models import (Appointment, AppointmentDocuments,
                     AppointmentPrescription, AppointmentVital,
                     CancellationReason, Feedbacks, HealthPackageAppointment,
                     PrescriptionDocuments, PrimeBenefits)

logger = logging.getLogger('django.serializers')

class CancellationReasonSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = CancellationReason
        fields = '__all__'


class AppointmentSerializer(DynamicFieldsModelSerializer):
    is_cancellable = serializers.ReadOnlyField()
    is_payment_option_enabled = serializers.ReadOnlyField()

    class Meta:
        model = Appointment
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.doctor:
            response_object['doctor'] = DoctorSerializer(instance.doctor).data

        if instance.patient:
            response_object['patient'] = PatientSerializer(
                instance.patient).data

        if instance.family_member:
            response_object['family_member'] = FamilyMemberSerializer(
                instance.family_member).data

        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(
                instance.hospital).data

        if instance.department:
            response_object['department_code'] = Department.objects.filter(id=instance.department.id).first().code

        if instance.reason:
            response_object["reason"] = CancellationReasonSerializer(
                instance.reason).data

        documents = AppointmentDocuments.objects.filter(
            appointment_info=instance.id)

        response_object["documents"] = AppointmentDocumentsSerializer(
            documents, many=True, fields=('document', 'document_type', 'name')).data

        vitals = AppointmentVital.objects.filter(appointment_info=instance.id)
        response_object["vitals"] = AppointmentVitalSerializer(
            vitals, many=True, fields=('blood_pressure', 'body_temperature', 'height', 'weight')).data

        return response_object


class HealthPackageAppointmentSerializer(DynamicFieldsModelSerializer):
    is_cancellable = serializers.ReadOnlyField()

    class Meta:
        model = HealthPackageAppointment
        fields = '__all__'

    def create(self, validated_data):
        health_package = validated_data.pop("health_package")
        appointment = HealthPackageAppointment.objects.create(**validated_data)
        appointment.health_package.set(health_package)
        health_package = HealthPackageSpecificSerializer(appointment.health_package, context={
            "hospital": appointment.hospital
        }, fields=['id', 'name', 'included_health_tests_count', 'pricing','image'],
            many=True).data
        for package in health_package:
            if package.get("pricing"):
                if package.get("pricing").get("hospital"):
                    package["pricing"]["hospital"] = str(
                        package.get("pricing").get("hospital"))
                if package.get("pricing").get("health_package"):
                    package["pricing"]["health_package"] = str(
                        package.get("pricing").get("health_package"))
        appointment.health_package_original = {
            "health_package": health_package}
        appointment.save()
        return appointment


class HealthPackageAppointmentDetailSerializer(DynamicFieldsModelSerializer):
    from apps.payments.serializers import PaymentSerializer
    hospital = HospitalSerializer(read_only=True)
    is_cancellable = serializers.ReadOnlyField()
    payment = PaymentSerializer(read_only=True)
    health_package = HealthPackageSpecificSerializer(read_only=True, many=True)
    is_cancellable = serializers.ReadOnlyField()
    reason = CancellationReasonSerializer(read_only=True)

    class Meta:
        model = HealthPackageAppointment
        fields = '__all__'

    def to_representation(self, instance):
        self.context["hospital"] = instance.hospital
        response_object = super().to_representation(instance)
        if instance.patient:
            response_object['patient'] = PatientSerializer(
                instance.patient).data

        if instance.family_member:
            response_object['family_member'] = FamilyMemberSerializer(
                instance.family_member).data

        return response_object


class AppointmentDocumentsSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = AppointmentDocuments
        fields = '__all__'
        extra_kwargs = {
            'name': {"error_messages": {"required": "Name is mandatory to upload your document."}},
        }

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        try:
            if instance.document:
                response_object['document'] = generate_pre_signed_url(
                    instance.document.url)
        except Exception as error:
            logger.error("Exception in PrescriptionDocumentsSerializer %s"%(str(error)))
            response_object['document'] = None

        return response_object


class AppointmentVitalSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = AppointmentVital
        fields = '__all__'


class PrescriptionDocumentsSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = PrescriptionDocuments
        fields = '__all__'
        extra_kwargs = {
            'name': {"error_messages": {"required": "Name is mandatory to upload your document."}},
        }

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        try:
            if instance.prescription:
                response_object['prescription'] = generate_pre_signed_url(
                    instance.prescription.url)
        except Exception as error:
            logger.error("Exception in PrescriptionDocumentsSerializer %s"%(str(error)))
            response_object['prescription'] = None

        return response_object


class FeedbacksSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Feedbacks
        fields = '__all__'


class AppointmentPrescriptionSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = AppointmentPrescription
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if instance.prescription_documents:
            response_object["prescription_documents"] = PrescriptionDocumentsSerializer(
                instance.prescription_documents.all(), many=True).data

        if instance.appointment_info:
            response_object["appointment_info"] = AppointmentSerializer(
                instance.appointment_info).data
            response_object["episode_number"] = instance.appointment_info.episode_number

        return response_object


class FeedbacksDataSerializer(DynamicFieldsModelSerializer):
    user_id = PatientSerializer()

    class Meta:
        model = Feedbacks
        fields = '__all__' 


class PrimeBenefitsSerializer(DynamicFieldsModelSerializer):

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if instance.hospital_info:
            response_object["hospital_info"] = HospitalSerializer(
                                                    instance.hospital_info.all(),
                                                    fields=("id","code","description"), 
                                                    many=True
                                                ).data

        return response_object

    class Meta:
        model = PrimeBenefits
        fields = '__all__'