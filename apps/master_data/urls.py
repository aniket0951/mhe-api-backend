from django.conf.urls import url
from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (AmbulanceContactViewSet, CompanyViewSet, DepartmentsView,
                    DoctorsView, EmergencyContactViewSet, HealthPackagesView,
                    HospitalDepartmentViewSet, HospitalViewSet,
                    ItemsTarrifPriceView, LabRadiologyItemsView,
                    PatientAppointmentStatus, RequestSyncView,
                    SpecialisationViewSet, ValidateMobileOTPView,
                    ValidateMobileView, ValidateOTPView, ValidateUHIDView)

router = DefaultRouter(trailing_slash=False)

router.register('all_hospitals', HospitalViewSet)
router.register('all_hospital_departments', HospitalDepartmentViewSet)
router.register('all_specialisations', SpecialisationViewSet)
router.register('all_ambulance_contacts', AmbulanceContactViewSet)
router.register('all_companies', CompanyViewSet)
router.register('emergency_contact', EmergencyContactViewSet)


urlpatterns = [

    url('^departments', DepartmentsView.as_view(),
        name="departments"),

    url('^doctors', DoctorsView.as_view(),
        name="doctors"),

    url('^health_packages', HealthPackagesView.as_view(),
        name="health_packages"),

    url('^lab_and_radiology_items', LabRadiologyItemsView.as_view(),
        name="lab_and_radiology"),

    url('^items_tariff_price', ItemsTarrifPriceView.as_view(),
        name="lab_and_radiology"),

    url('^generate_uhid_otp', ValidateUHIDView.as_view(),
        name="validate_uhid"),

    url('^validate_uhid_otp', ValidateOTPView.as_view(),
        name="validate_otp"),

    url('^patient_app_statistics', PatientAppointmentStatus.as_view(),
        name="patient_app_statistics"),

    url('^request_sync', RequestSyncView.as_view()),

    url('^generate_mobile_otp', ValidateMobileView.as_view(),
        name="validate_mobile"),

    url('^validate_mobile_otp', ValidateMobileOTPView.as_view(),
        name="validate_mobile_otp"),

    * router.urls
]
