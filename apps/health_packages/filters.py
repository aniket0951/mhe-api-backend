from django_filters.rest_framework import BaseInFilter, UUIDFilter, FilterSet
from .models import HealthPackage
class UUIDInFilter(BaseInFilter, UUIDFilter):
    pass


class HealthPackageFilter(FilterSet):
    specialisation_id_in = UUIDInFilter(field_name='specialisation__id', lookup_expr='in')

    class Meta:
        model = HealthPackage
        fields = ['specialisation_id_in', ]