from django.conf.urls import url
from django.urls import path

from .views import (ManipalAdminResetPasswordView, change_password,
                    forgot_password, login)

app_name = 'manipal_admin'

urlpatterns = [
    url(r'^login', login, name='login'),
    url(r'^forgot_password', forgot_password, name='forgot_password'),
    url(r'^change_password',
        change_password, name='change_password'),
    path("reset_password/<uidb64>/<token>",
         ManipalAdminResetPasswordView.as_view(), name="password_reset"),
]
