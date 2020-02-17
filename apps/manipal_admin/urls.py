from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^api/admin/login/', views.login, name='login'),
    url(r'^api/admin/change_password/', views.change_password, name='change_password'),
]