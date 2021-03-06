from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PatientPersonalDocumentsViewSet

app_name = 'personl_documents'

router = DefaultRouter(trailing_slash=False)

router.register('', PatientPersonalDocumentsViewSet)


urlpatterns = [
    *router.urls
]
