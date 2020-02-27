from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    path('doctors/', views.DoctorsAPIView.as_view()),
    path('location/', views.LocationAPIView.as_view()),
    path('preferred_location/', views.PreferredLocationView,
         name="PreferredLocationView"),
    path('doctors_list_view/', views.DoctorsListView.as_view()),
    path('doctor_details/', views.DoctorSlotAvailability.as_view()),
    path('departments/', views.DepartmentAPIView.as_view()),

]
