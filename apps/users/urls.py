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
    url(r'^api/user/change_mobile_number/', views.change_mobile_number, name='change_mobile_number'),
    url(r'^api/user/set_gender/', views.set_gender, name='set_gender'),
    url(r'^api/user/add_family_member/', views.add_family_member, name='add_family_member'),
    url(r'^api/user/edit_family_member/', views.edit_family_member, name='edit_family_member'),
    url(r'^api/user/list_family_members/', views.list_family_members, name='list_family_members'),
    url(r'^api/user/delete_family_member/', views.delete_family_member, name='delete_family_member'),
    url(r'^api/user/set_favorite_hospital/', views.set_favorite_hospital, name='set_favorite_hospital'),
    url(r'^api/user/add_family_member_verification/', views.add_family_member_verification, name='add_family_member_verification'),

]	
