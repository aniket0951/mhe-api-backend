from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ValidationError

from utils import custom_viewsets
from utils.custom_permissions import (BlacklistDestroyMethodPermission,
                                      BlacklistUpdateMethodPermission,
                                      IsManipalAdminUser)

from .models import HealthPackage, HealthPackageCategory, HealthPackagePricing
from .serializers import (HealthPackageCategoryDetailSerializer,
                          HealthPackageCategorySerializer,
                          HealthPackageDetailSerializer,
                          HealthPackageSerializer)


class HealthPackageCategoryViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = HealthPackageCategory
    queryset = HealthPackageCategory.objects.all()
    serializer_class = HealthPackageCategorySerializer
    detail_serializer_class = HealthPackageCategoryDetailSerializer
    create_success_message = "New health package category is added successfully."
    list_success_message = 'Health package category list returned successfully!'
    retrieve_success_message = 'Health package category information returned successfully!'
    update_success_message = 'hHealth package category information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    # search_fields = ['code', 'description', ]
    ordering_fields = ('code',)

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
        hospital_related_health_packages = HealthPackagePricing.objects.filter(
            hospital=hospital_id).values_list('health_package_id', flat=True)
        return HealthPackageCategory.objects.filter(health_package__id__in=hospital_related_health_packages)



class HealthPackageViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = HealthPackage
    queryset = HealthPackage.objects.all()
    serializer_class = HealthPackageSerializer
    detail_serializer_class = HealthPackageDetailSerializer
    create_success_message = "New health package is added successfully."
    list_success_message = 'Health package list returned successfully!'
    retrieve_success_message = 'Health package information returned successfully!'
    update_success_message = 'hHealth package information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    # search_fields = ['code', 'description', ]
    ordering_fields = ('code',)

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
        hospital_related_health_packages = HealthPackagePricing.objects.filter(
            hospital=hospital_id).values_list('health_package_id', flat=True)
        return HealthPackage.objects.filter(id__in=hospital_related_health_packages)
