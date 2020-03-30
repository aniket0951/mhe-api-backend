from django_filters.rest_framework import (BaseInFilter, BooleanFilter,
                                           FilterSet, UUIDFilter)

from .models import HealthPackage


class UUIDInFilter(BaseInFilter, UUIDFilter):
    pass


class HealthPackageFilter(FilterSet):
    specialisation_id_in = UUIDInFilter(
        field_name='specialisation__id', lookup_expr='in')
    id_not = UUIDFilter(field_name='id', exclude=True)
    is_popular = BooleanFilter(field_name='is_popular')

    class Meta:
        model = HealthPackage
        fields = {
            'specialisation_id_in': ['exact'],
            'id_not': ['exact']
        }
