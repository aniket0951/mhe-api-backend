from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from apps.master_data.models import Hospital
from apps.health_packages.models import HealthPackagePricing
from utils import custom_viewsets
from utils.custom_permissions import (IsManipalAdminUser, IsPatientUser,
                                      IsSelfHealthPackageCartItem,
                                      IsSelfHomeCollectionCartItem)
from utils.utils import manipal_admin_object, patient_user_object

from .models import HealthPackageCart, HomeCollectionCart
from .serializers import (HealthPackageCartSerializer,
                          HomeCollectionCartSerializer)


class HealthPackageCartViewSet(custom_viewsets.ListUpdateViewSet):
    permission_classes = [IsAuthenticated]
    model = HealthPackageCart
    queryset = HealthPackageCart.objects.all()
    serializer_class = HealthPackageCartSerializer
    create_success_message = "Health packages added to your cart successfully."
    list_success_message = 'Cart items returned successfully!'
    retrieve_success_message = 'Cart items information returned successfully!'
    update_success_message = 'Your cart is updated successfuly!'
    delete_success_message = 'Items from your cart deleted successfuly!'

    def get_permissions(self):
        if self.action in ['list', ]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', ]:
            permission_classes = [IsPatientUser, IsSelfHealthPackageCartItem]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        return super().get_queryset().filter(patient_info_id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        patient_user = patient_user_object(request)
        cart_obj = self.get_queryset().filter(patient_info=patient_user,).first()
        
        if not cart_obj:
            cart_obj = self.model.objects.create(
                patient_info=patient_user,
                hospital=Hospital.objects.first()
            )

        data = {
            "data": self.get_serializer(cart_obj).data,
            "message": self.list_success_message,
        }
        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):

        data = request.data
        health_packages = data.get('health_packages')
        hospital = data.get("hospital")
        
        try:
            hospital_id = Hospital.objects.get(id=hospital)
        except Exception as e:
                raise ValidationError("Hospital is mandatory")

        for health_package in health_packages:
            try:
                HealthPackagePricing.objects.get(health_package=health_package,hospital=hospital)
            except Exception as e:
                raise ValidationError("You cannot add health packages that don't belong to %s"%(str(hospital_id.description)))
        
        return super().update(request, *args, **kwargs)

class HomeCollectionCartViewSet(custom_viewsets.ListUpdateViewSet):
    permission_classes = [IsAuthenticated]
    model = HomeCollectionCart
    queryset = HomeCollectionCart.objects.all()
    serializer_class = HomeCollectionCartSerializer
    list_success_message = 'Cart items returned successfully!'
    update_success_message = 'Your cart is updated successfuly!'

    def get_permissions(self):
        if self.action in ['list', ]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', ]:
            permission_classes = [IsPatientUser, IsSelfHomeCollectionCartItem]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        return super().get_queryset().filter(patient_info_id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        patient_user = patient_user_object(request)
        cart_obj = self.get_queryset().filter(patient_info=patient_user,).first()

        if not cart_obj:
            cart_obj = self.model.objects.create(
                patient_info=patient_user,
                hospital=Hospital.objects.first()
            )

        data = {
            "data": self.get_serializer(cart_obj).data,
            "message": self.list_success_message,
        }
        return Response(data, status=status.HTTP_200_OK)
