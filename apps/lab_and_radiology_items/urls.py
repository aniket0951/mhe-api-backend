from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import HomeCollectionViewSet

app_name = 'home_care'

router = DefaultRouter(trailing_slash=False)

router.register('home_collection', HomeCollectionViewSet)


urlpatterns = [
    # path('change_password', UsersChangePasswordView.as_view(),
    #      name='thinkahoy_user_change_password'),
    *router.urls
]
