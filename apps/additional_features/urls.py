from django.urls.conf import path
from rest_framework.routers import DefaultRouter

from .views import DriveScheduleViewSet, StaticInstructionsViewSet, DriveItemCodePriceView,DriveInventoryViewSet, DriveBookingViewSet

app_name = 'additional_features'


router = DefaultRouter(trailing_slash=False)

router.register('static_instructions', StaticInstructionsViewSet)
router.register('', DriveScheduleViewSet)
router.register('drive_inventory', DriveInventoryViewSet)
router.register('drive_booking', DriveBookingViewSet)

urlpatterns = [
     path('item_price', DriveItemCodePriceView.as_view()),
     * router.urls

]
