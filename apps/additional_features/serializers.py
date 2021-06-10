from utils.serializers import DynamicFieldsModelSerializer
from .models import StaticInstructions
        
class StaticInstructionsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = StaticInstructions
        fields = '__all__'       

