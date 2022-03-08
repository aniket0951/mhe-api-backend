from django.urls import path
from .views import shortView, redirect_url_view

urlpatterns = [
    path("api/url_shortner/", shortView, name="url_shortner"),
    path('<str:shortened_part>', redirect_url_view, name="url_redirector"),
]
