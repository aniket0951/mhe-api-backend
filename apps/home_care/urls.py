from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import HealthTestViewSet, HealthTestPricingViewSet, HealthTestCartItemViewSet, LabTestAppointmentHistoryViewSet, LabTestAppointmentViewSet, LabTestSlotScheduleViewSet, LabTestSlotsWeeklyMasterViewSet

app_name = 'home_care'

router = DefaultRouter(trailing_slash=False)

router.register('health_test', HealthTestViewSet)
router.register('health_test_pricing', HealthTestPricingViewSet)
router.register('health_test_appointment', LabTestAppointmentViewSet)
router.register('health_test_cart_item', HealthTestCartItemViewSet)
router.register('lab_test_weekly_slot', LabTestSlotsWeeklyMasterViewSet)
router.register('lab_test_slot_schedule', LabTestSlotScheduleViewSet)
router.register('health_test_appointment_history', LabTestAppointmentHistoryViewSet)

urlpatterns = [  
    *router.urls
]