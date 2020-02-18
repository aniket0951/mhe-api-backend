from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    path('doctors/', views.DoctorsAPIView.as_view()),
    path('location/', views.LocationAPIView.as_view()),
    path('specialisation/', views.SpecialisationAPIView.as_view()),
    path('doctorDetails/', views.DoctorDetailView, name="doctorview"),
    path('PreferredLocation/', views.PreferredLocationView,
         name="PreferredLocationView"),
    path('doctorsListView/', views.DoctorsListView.as_view()),

]
