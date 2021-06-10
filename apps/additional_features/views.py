from .serializers import StaticInstructionsSerializer
from .models import StaticInstructions
from utils import custom_viewsets
from rest_framework.permissions import IsPatientUser


class StaticInstructionsViewSet(custom_viewsets.ReadOnlyModelViewSet):
    queryset = StaticInstructions.objects.all()
    serializer_class = StaticInstructionsSerializer
    permission_classes = [IsPatientUser]
    create_success_message = None
    list_success_message = 'Static Instructions returned successfully!'
    retrieve_success_message = 'Static Instruction returned successfully!'
    update_success_message = None