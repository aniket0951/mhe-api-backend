from rest_framework import serializers

from apps.appointments.models import Appointment
from utils.serializers import DynamicFieldsModelSerializer
from .models import Payment


class PaymentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
