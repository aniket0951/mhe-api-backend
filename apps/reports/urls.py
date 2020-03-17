
from django.conf.urls import url
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ReportsSyncAPIView, ReportViewSet, NumericReportDetailsViewSet
router = DefaultRouter(trailing_slash=False)

router.register('', ReportViewSet)


urlpatterns = [

    url('^sync', ReportsSyncAPIView.as_view(),
        name="sync_reports"),

    *router.urls
]
