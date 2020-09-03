
from django.conf.urls import url
from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (NumericReportDetailsViewSet, PrescriptionDocumentsViewSet,
                    ReportsSyncAPIView, ReportViewSet, ReportVisitViewSet)

router = DefaultRouter(trailing_slash=False)

router.register('', ReportViewSet)
router.register('report_download', PrescriptionDocumentsViewSet)
router.register('report_visit', ReportVisitViewSet)


urlpatterns = [

    url('^sync', ReportsSyncAPIView.as_view(),
        name="sync_reports"),

    *router.urls
]
