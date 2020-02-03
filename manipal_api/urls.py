from django.urls import path, include, url
from apps.appointments import views
from rest_framework import routers



urlpatterns = [
    url(r'^', include(('apps.users.urls', 'users'), namespace='users')),
    path('admin/', admin.site.urls),
    path('appointment/', include('apps.doctors.urls')),
    path('myAppointment/', include('apps.appointments.urls')),

    
]
