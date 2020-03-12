
from django.urls import path

from rest_framework import routers
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter(trailing_slash=False)





urlpatterns = [
    path('get_data',getData, name = "getData"),
    path('get_response', getResponse, name = "getResponse"),

]

