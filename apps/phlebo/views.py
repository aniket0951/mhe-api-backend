from rest_framework.permissions import AllowAny
from apps.phlebo.models import Phlebo
from apps.phlebo.serializers import PhleboSerializer
from utils import custom_viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.serializers import ValidationError
from rest_framework.response import Response

class PhleboAPIView(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    model = Phlebo
    queryset = Phlebo.objects.all()
    serializer_class = PhleboSerializer
    
    create_success_message = 'Phlebo registered successfully!'
    update_success_message = 'Phlebo information updated successfully!'
    list_success_message = "Phlebo information returned successfully"
    retrieve_success_message = "Phlebo information retrieved successfully"

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    ordering_fields = ('-created_at',)

    def create(self, request):
        mobile = request.data.get('mobile')
        email = request.data.get("email")
        if not mobile:
            raise ValidationError("Mobile is mandatory")
        if not email:
            raise ValidationError("Email is mandatory")
      
        request.data['is_active'] = True
        admin_object = self.serializer_class(data = request.data)
        admin_object.is_valid(raise_exception=True)
        admin_object.save()
        if request.data.get('password'):
            user_object = Phlebo.objects.filter(email=email).first()
            user_object.set_password(request.data.get('password'))
            user_object.save()
        return Response(status=status.HTTP_200_OK)
    