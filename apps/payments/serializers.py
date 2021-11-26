import logging
from apps.appointments.models import Appointment
from apps.appointments.serializers import (AppointmentSerializer,
                                           HealthPackageAppointmentSerializer)
from apps.health_packages.models import HealthPackage
from apps.health_packages.serializers import HealthPackageDetailSerializer
from apps.master_data.models import Hospital
from apps.master_data.serializers import HospitalSerializer
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url

from .models import Payment, PaymentReceipts, PaymentRefund, UnprocessedTransactions

logger = logging.getLogger("django")

class PaymentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Payment
        exclude = ('raw_info_from_salucro_response', 'updated_at')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if instance.appointment:
            response_object['appointment'] = AppointmentSerializer(
                instance.appointment).data

        if instance.health_package_appointment:
            response_object['health_package_appointment'] = HealthPackageAppointmentSerializer(
                instance.health_package_appointment).data

        if instance.patient:
            response_object['patient'] = PatientSerializer(
                instance.patient).data

        if instance.payment_done_for_family_member:
            response_object['payment_done_for_family_member'] = FamilyMemberSerializer(
                instance.payment_done_for_family_member).data

        if instance.payment_done_for_patient:
            response_object['payment_done_for_patient'] = PatientSerializer(
                instance.payment_done_for_patient).data

        if instance.location:
            response_object['location'] = HospitalSerializer(
                instance.location).data

        response_object["refund"] = None

        if instance.payment_refund.exists():
            payment_instance = instance.payment_refund.filter(status="success").first()
            if payment_instance:
                response_object["refund"] = PaymentSpecificRefundSerializer(payment_instance).data

        response_object["unprocessed_transaction"] = None

        if instance.unprocessed_transactions_payment.exists():
            unprocessed_transaction_instance = instance.unprocessed_transactions_payment.first()
            if unprocessed_transaction_instance:
                response_object["unprocessed_transaction"] = UnprocessedTransactionsSerializer(unprocessed_transaction_instance,fields=("id","retries","status")).data

        response_object["receipt"] = None

        receipts = PaymentReceipts.objects.filter(
            payment_info=instance.id).first()

        response_object["receipt"] = PaymentReceiptsSerializer(
            receipts).data

        return response_object


class PaymentRefundSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PaymentRefund
        exclude = ('updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if instance.payment:
            response_object['payment'] = PaymentSerializer(
                instance.payment).data

        return response_object


class PaymentSpecificRefundSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PaymentRefund
        exclude = ('updated_at', 'payment', 'created_at', 'uhid_number')


class UnprocessedTransactionsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = UnprocessedTransactions
        fields = '__all__'
        
    def to_representation(self, instance):
        return super().to_representation(instance)


class PaymentReceiptsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PaymentReceipts
        exclude = ('updated_at', 'created_at')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        try:
            if instance.receipt:
                response_object['receipt'] = generate_pre_signed_url(
                    instance.receipt.url)
        except Exception as error:
            logger.error("Exception in PaymentReceiptsSerializer: %s"%(str(error)))
            response_object['receipt'] = None
        return response_object
