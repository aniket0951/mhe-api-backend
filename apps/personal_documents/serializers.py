from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url

from .models import PatientPersonalDocuments
from rest_framework import serializers

from apps.patients.serializers import CurrentPatientUserDefault


class PatientPersonalDocumentsSerializer(DynamicFieldsModelSerializer):
    patient_info = serializers.UUIDField(write_only=True,
                                         default=CurrentPatientUserDefault())

    class Meta:
        model = PatientPersonalDocuments
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
            print(error)
            response_object['display_picture'] = None

        return response_object
