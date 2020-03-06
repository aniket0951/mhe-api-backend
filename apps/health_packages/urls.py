from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import HealthPackageCategoryViewSet, HealthPackageViewSet

app_name = 'health_package'

router = DefaultRouter(trailing_slash=False)

router.register('category', HealthPackageCategoryViewSet)
router.register('', HealthPackageViewSet)


urlpatterns = [
    # path('change_password', UsersChangePasswordView.as_view(),
    #      name='thinkahoy_user_change_password'),
    *router.urls
]
