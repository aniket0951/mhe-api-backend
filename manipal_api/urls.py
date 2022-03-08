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
    path('api/payments/', include('apps.payments.urls')),
    path('api/patient_registration/', include('apps.patient_registration.urls')),
    path('api/personal_documents/', include('apps.personal_documents.urls')),
    path('api/cart_items/', include('apps.cart_items.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/video_conferences/', include('apps.video_conferences.urls')),
    path('api/discharge_summaries/', include('apps.discharge_summaries.urls')),
    path('api/additional_features/', include('apps.additional_features.urls')),
    path('', include('apps.url_shortner.urls')),
]
