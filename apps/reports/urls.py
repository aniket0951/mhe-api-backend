
from django.conf.urls import url
from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (NumericReportDetailsViewSet, PrescriptionDocumentsViewSet,
                    ReportsSyncAPIView, ReportViewSet)

router = DefaultRouter(trailing_slash=False)

router.register('', ReportViewSet)
router.register('report_download', PrescriptionDocumentsViewSet)


urlpatterns = [

    url('^sync', ReportsSyncAPIView.as_view(),
        name="sync_reports"),

    *router.urls
]
