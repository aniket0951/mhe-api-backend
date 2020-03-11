from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ValidationError

from apps.master_data.models import BillingGroup
from utils import custom_viewsets
from utils.custom_permissions import (BlacklistDestroyMethodPermission,
                                      BlacklistUpdateMethodPermission,
                                      IsManipalAdminUser)

from .models import LabRadiologyItem, LabRadiologyItemPricing
from .serializers import LabRadiologyItemSerializer


class HomeCollectionViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = LabRadiologyItem
    queryset = LabRadiologyItem.objects.all()
    serializer_class = LabRadiologyItemSerializer
    detail_serializer_class = LabRadiologyItemSerializer
    create_success_message = "New health package is added successfully."
    list_success_message = 'Health package list returned successfully!'
    retrieve_success_message = 'Health package information returned successfully!'
    update_success_message = 'hHealth package information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['name', ]
    ordering_fields = ('health_package_pricing__price',)
    # filter_fields = ('specialisation',)

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'create']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            if hasattr(self, 'detail_serializer_class'):
                return self.detail_serializer_class
        return super().get_serializer_class()

    def get_queryset(self):
        hospital_id = self.request.query_params.get('hospital__id')
        if not hospital_id:
            raise ValidationError("Hospital ID is missiing!")

        home_collection_billing_group = BillingGroup.objects.filter(
            description='Lab Diagnostic Services').first()

        hospital_related_items = LabRadiologyItemPricing.objects.filter(
            hospital=hospital_id).values_list('item_id', flat=True)

        return LabRadiologyItem.objects.filter(id__in=hospital_related_items,
                                               billing_group=home_collection_billing_group)
