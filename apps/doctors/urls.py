from django.conf.urls import url

from . import views

# from rest_framework import routers

# router = routers.SimpleRouter()
# router.register(r'slave', views.SlaveViewSet, "Slave")

urlpatterns = [
    url(r'^appointments/', views.appointment, name='appointment'),
]

# urlpatterns += router.urls