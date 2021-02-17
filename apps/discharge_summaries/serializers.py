import logging
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import patient_user_object, generate_pre_signed_url
from .models import DischargeSummary

logger = logging.getLogger("django")

class DischargeSummarysSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = DischargeSummary
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        try:
            if instance.discharge_document:
                response_object['discharge_document'] = generate_pre_signed_url(
                    instance.discharge_document.url)
            
        except Exception as error:
            logger.info("Exception in DischargeSummarysSerializer: %s"%(str(error)))
            response_object['discharge_document'] = None

        return response_object