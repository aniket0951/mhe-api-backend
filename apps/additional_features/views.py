from .serializers import StaticInstructionsSerializer
from .models import StaticInstructions
from utils import custom_viewsets
from utils.custom_permissions import IsPatientUser


class StaticInstructionsViewSet(custom_viewsets.ReadOnlyModelViewSet):
    queryset = StaticInstructions.objects.all()
    serializer_class = StaticInstructionsSerializer
    permission_classes = [IsPatientUser]
    list_success_message = 'Static Instructions returned successfully!'
    retrieve_success_message = 'Static Instruction returned successfully!'
