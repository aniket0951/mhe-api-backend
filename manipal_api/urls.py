from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from apps.appointments import views

urlpatterns = [
    path('', include(('apps.users.urls', 'users'), namespace='users')),
    path('admin/', admin.site.urls),
    path('appointment/', include('apps.doctors.urls')),
    path('myAppointment/', include('apps.appointments.urls')),

    
]
