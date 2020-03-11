from django.contrib import admin
from django.urls import include, path
from rest_framework_jwt.views import refresh_jwt_token

urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api/refresh', refresh_jwt_token),
    path('api/patients/', include('apps.patients.urls')),
    path('api/manipal_admin/', include('apps.manipal_admin.urls')),
    path('api/doctors/', include('apps.doctors.urls')),
    path('api/appointments/', include('apps.appointments.urls')),
    path('api/master_data/', include('apps.master_data.urls')),
    path('api/health_packages/', include('apps.health_packages.urls')),
    path('api/home_care/', include('apps.lab_and_radiology_items.urls')),



]
