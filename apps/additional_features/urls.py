from apps.doctors import views
from django.urls.conf import path
from rest_framework.routers import DefaultRouter
from .views import DriveScheduleViewSet, StaticInstructionsViewSet
<<<<<<< HEAD
from . import views
=======
>>>>>>> dev

router = DefaultRouter(trailing_slash=False)

router.register('static_instructions', StaticInstructionsViewSet)
router.register('drive_schedule', DriveScheduleViewSet)

urlpatterns = [
     path('item_price', views.DriveItemCodePriceView.as_view()),
     * router.urls
]