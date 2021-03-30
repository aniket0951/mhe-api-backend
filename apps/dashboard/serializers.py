import logging
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url
from .models import DashboardBanner, FAQData

logger = logging.getLogger('django')

class DashboardBannerSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = DashboardBanner
        exclude = ('created_at', 'updated_at')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        try:
            if instance.image:
                response_object['image'] = generate_pre_signed_url(
                    instance.image.url)
        except Exception as error:
            logger.info("Exception in DashboardBannerSerializer: %s"%(str(error)))
            response_object['image'] = None
        return response_object

class FAQDataSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FAQData
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        try:
            if instance.image:
                response_object['image'] = generate_pre_signed_url(instance.image.url)
        except Exception as error:
            logger.info("Exception in FAQDataSerializer: %s"%(str(error)))
            response_object['image'] = None
        return response_object