from datetime import datetime

from django.db.models import Exists, OuterRef, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ValidationError

from apps.cart_items.models import HealthPackageCart
from apps.master_data.models import Specialisation
from utils import custom_viewsets
from utils.custom_permissions import (BlacklistDestroyMethodPermission,
                                      BlacklistUpdateMethodPermission,
                                      IsManipalAdminUser)

from .filters import HealthPackageFilter
from .models import HealthPackage, HealthPackagePricing
from .serializers import (HealthPackageDetailSerializer,
                          HealthPackageSerializer,
                          HealthPackageSpecialisationDetailSerializer,
                          HealthPackageSpecialisationSerializer)


class HealthPackageSpecialisationViewSet(custom_viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    model = Specialisation
    queryset = Specialisation.objects.all()
    serializer_class = HealthPackageSpecialisationSerializer
    detail_serializer_class = HealthPackageSpecialisationDetailSerializer
    create_success_message = "New health package specialisation is added successfully."
    list_success_message = 'Health package specialisation list returned successfully!'
    retrieve_success_message = 'Health package specialisation information returned successfully!'
    update_success_message = 'Health package specialisation information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    ordering_fields = ('description',)
    search_fields = ('description', 'code')

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve' and hasattr(self, 'detail_serializer_class'):
            return self.detail_serializer_class
        return super().get_serializer_class()

    def get_queryset(self):
        hospital_id = self.request.query_params.get('hospital__id')
        if not hospital_id:
            raise ValidationError("Hospital ID is missing!")
        hospital_related_health_packages = HealthPackagePricing.objects.filter(
            hospital=hospital_id).values_list('health_package_id', flat=True)
        return Specialisation.objects.filter(health_package__id__in=hospital_related_health_packages).filter(
            Q(end_date__gte=datetime.now()) | Q(end_date__isnull=True)).distinct('description',)


class HealthPackageViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = HealthPackage
    queryset = HealthPackage.objects.all()
    serializer_class = HealthPackageSerializer
    detail_serializer_class = HealthPackageDetailSerializer
    create_success_message = "New health package is added successfully."
    list_success_message = 'Health package list returned successfully!'
    retrieve_success_message = 'Health package information returned successfully!'
    update_success_message = 'Health package information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    filter_class = HealthPackageFilter
    search_fields = ['name', 'code']
    ordering_fields = ('health_package_pricing__price', 'name')

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
        if self.action == 'retrieve' and hasattr(self, 'detail_serializer_class'):
            return self.detail_serializer_class
        return super().get_serializer_class()

    def get_queryset(self):
        hospital_id = self.request.query_params.get('hospital__id')
        if not hospital_id:
            raise ValidationError("Hospital ID is missiing!")
        hospital_related_health_packages = HealthPackagePricing.objects.filter(
            hospital=hospital_id).values_list('health_package_id', flat=True)

        user_cart_packages = HealthPackageCart.objects.filter(
            patient_info_id=self.request.user.id,  health_packages=OuterRef('pk'), hospital_id=hospital_id)

        return HealthPackage.objects.filter(id__in=hospital_related_health_packages)\
            .distinct().annotate(is_added_to_cart=Exists(user_cart_packages))
