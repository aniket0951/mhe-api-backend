import logging

from django.http import response
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url
from .models import DashboardBanner, FAQData, FlyerImages, FlyerScheduler

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

class FlyerSchedulerSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FlyerScheduler
        exclude = ('created_at', 'updated_at', 'created_by', 'updated_by')

    def to_representation(self, instance):
        response_opject = super().to_representation(instance)
        flyer_image_ids = FlyerImages.objects.filter(flyer_scheduler_id=instance.id)
        response_opject['flyer_images'] = FlyerImagesSerializer(flyer_image_ids,many=True).data
        return response_opject

class FlyerImagesSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = FlyerImages
        exclude = ('created_at', 'updated_at', 'created_by', 'updated_by')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        try:
            if instance.image:
                response_object['image'] = generate_pre_signed_url(
                    instance.image.url)
        except Exception as error:
            logger.info("Exception in FlyerImagesSerializer : %s"%(str(error)))
            response_object['image'] = None
        return response_object