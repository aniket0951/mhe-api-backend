from django.conf.urls import url
from . import views
from django.urls import path

urlpatterns = [
    path('doctors/', views.DoctorsAPIView.as_view()),
    path('location/', views.LocationAPIView.as_view()),
    path('department/', views.DepartmentAPIView.as_view()),
    path('doctorIn/', views.DoctorDetailView, name = "doctorview"),
    path('PreferredLocation/', views.PreferredLocationView, name = "PreferredLocationView"),
]