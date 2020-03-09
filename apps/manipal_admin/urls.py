from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^login', views.login, name='login'),
    url(r'^change_password',
        views.change_password, name='change_password'),
]
