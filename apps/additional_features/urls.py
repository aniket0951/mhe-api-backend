from rest_framework.routers import DefaultRouter
from .views import DriveScheduleViewSet, StaticInstructionsViewSet


router = DefaultRouter(trailing_slash=False)

router.register('static_instructions', StaticInstructionsViewSet)
router.register('drive_schedule', DriveScheduleViewSet)

urlpatterns = [
     * router.urls

]
