from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^api/admin/login/', views.login, name='login'),
    url(r'^api/admin/reset_password/', views.reset_password, name='reset_password'),
]