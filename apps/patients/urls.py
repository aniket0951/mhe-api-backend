from django.urls import path

from apps.patients.views import (
                        CovidVaccinationRegistrationView,
                        FamilyMemberViewSet, 
                        PatientAddressViewSet,
                        PatientViewSet, 
                        SendSms
                    )
from rest_framework.routers import DefaultRouter

app_name = 'patients'

router = DefaultRouter(trailing_slash=False)

router.register('family_members', FamilyMemberViewSet)
router.register('address', PatientAddressViewSet)
router.register('vaccine_registration', CovidVaccinationRegistrationView)
router.register('', PatientViewSet)

urlpatterns = [
    # path('change_password', UsersChangePasswordView.as_view(),
    #      name='thinkahoy_user_change_password'),
    path('send_sms', SendSms.as_view()),
    *router.urls
]
