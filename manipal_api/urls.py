from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from apps.appointments import views


urlpatterns = [
    path('', include(('apps.users.urls', 'users'), namespace='users')),
    path('', include(('apps.manipal_admin.urls', 'manipal_admin'), namespace='manipal_admin')),
    path('admin/', admin.site.urls),
    path('api/appointment/', include('apps.doctors.urls')),
    path('api/myAppointment/', include('apps.appointments.urls')),
    path('api/master_data/', include('apps.master_data.urls')),

]
