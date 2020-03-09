from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.patients.views import FamilyMemberViewSet, PatientViewSet

app_name = 'patients'

router = DefaultRouter(trailing_slash=False)

router.register('family_members', FamilyMemberViewSet)
router.register('', PatientViewSet)

urlpatterns = [
    # path('change_password', UsersChangePasswordView.as_view(),
    #      name='thinkahoy_user_change_password'),
    *router.urls
]
