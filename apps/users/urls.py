from django.conf.urls import url

from . import views

# from rest_framework import routers

# router = routers.SimpleRouter()
# router.register(r'slave', views.SlaveViewSet, "Slave")

urlpatterns = [
    url(r'^api/user/sign_up/', views.sign_up, name='sign_up'),
    url(r'^api/user/send_otp/', views.send_otp, name='send_otp'),
    url(r'^api/user/otp_verification/', views.otp_verification, name='otp_verification'),
    url(r'^api/user/login/', views.login, name='login'),
    url(r'^api/user/facebook_or_google_login/', views.facebook_or_google_login, name='facebook_or_google_login'),
    url(r'^api/user/facebook_or_google_signup/', views.facebook_or_google_signup, name='facebook_or_google_signup'),
    url(r'^api/user/change_mobile_number/', views.change_mobile_number, name='change_mobile_number')
]	