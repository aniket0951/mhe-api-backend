from django_filters.rest_framework import CharFilter, FilterSet

from .models import Report


class ReportFilter(FilterSet):
    code__startswith = CharFilter(field_name='code', lookup_expr='startswith')
    code__notstartswith = CharFilter(
        field_name='code', lookup_expr='startswith', exclude=True)

    class Meta:
        model = Report
        fields = ['numeric_report__identifier', 'patient_class', ]
