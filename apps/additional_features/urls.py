from django.urls.conf import path
from rest_framework.routers import DefaultRouter

from .views import DriveScheduleViewSet, StaticInstructionsViewSet
from . import views
from .views import DriveScheduleViewSet, StaticInstructionsViewSet, DriveItemCodePriceView

router = DefaultRouter(trailing_slash=False)

router.register('static_instructions', StaticInstructionsViewSet)
router.register('drive_schedule', DriveScheduleViewSet)

urlpatterns = [
     path('item_price', DriveItemCodePriceView.as_view()),
     * router.urls

]
