from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url

from .models import DashboardBanner


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
            print(error)
            response_object['image'] = None
        return response_object