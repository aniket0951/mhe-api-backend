from apps.doctors.serializers import HospitalSerializer
from apps.phlebo.models import Phlebo, PhleboRegion
from utils.serializers import DynamicFieldsModelSerializer

class PhleboSerializer(DynamicFieldsModelSerializer):
  
    class Meta:
        model = Phlebo
        exclude = ('password', 'last_login', 'is_superuser', 'updated_at',
                   'created_at', 'is_staff', 'is_active', 'groups', 'user_permissions')
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(instance.hospital).data
        return response_object
    
class PhleboRegionSerializer(DynamicFieldsModelSerializer):
  
    class Meta:
        model = PhleboRegion
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.phlebo:
            response_object['phlebo'] = PhleboSerializer(instance.phlebo).data
        return response_object