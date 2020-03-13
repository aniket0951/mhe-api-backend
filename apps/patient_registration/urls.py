from django.conf.urls import url
from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import RegistrationAPIView

router = DefaultRouter(trailing_slash=False)

urlpatterns = [
    path('', RegistrationAPIView.as_view()),
    
    *router.urls

]
