from django.conf.urls import url
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
                ManipalAdminResetPasswordView,
                change_password,
                forgot_password, 
                login,
                logout,
                AdminMenuView,
                AdminRoleView
            )

app_name = 'manipal_admin'

router = DefaultRouter(trailing_slash=False)
router.register('admin_menus',AdminMenuView)
router.register('admin_roles',AdminRoleView)

urlpatterns = [
    url(r'^login', login, name='login'),
    url(r'^logout', logout, name='logout'),
    url(r'^forgot_password', forgot_password, name='forgot_password'),
    url(r'^change_password', change_password, name='change_password'),
    path("reset_password/<uidb64>/<token>", ManipalAdminResetPasswordView.as_view(), name="password_reset"),
    * router.urls
]
