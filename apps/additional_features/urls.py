from rest_framework.routers import DefaultRouter
from .views import StaticInstructionsViewSet


router = DefaultRouter(trailing_slash=False)

router.register('static_instructions', StaticInstructionsViewSet)