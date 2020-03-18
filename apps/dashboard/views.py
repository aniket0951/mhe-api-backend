from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.manipal_admin.serializers import ManipalAdminSerializer
from apps.patients.serializers import PatientSerializer
from utils import custom_viewsets
from utils.custom_permissions import IsManipalAdminUser
from utils.utils import manipal_admin_object, patient_user_object

from .models import DashboardBanner
from .serializers import DashboardBannerSerializer


class DashboardBannerViewSet(custom_viewsets.CreateDeleteViewSet):
    permission_classes = [IsManipalAdminUser]
    model = DashboardBanner
    queryset = DashboardBanner.objects.all()
    serializer_class = DashboardBannerSerializer
    create_success_message = "New dashboard banner added successfully."
    delete_success_message = "Dashboard banner deleted successfully."


class DashboardAPIView(ListAPIView):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        dashboard_details = {}
        dashboard_details['banners'] = DashboardBannerSerializer(
            DashboardBanner.objects.all(), many=True).data

        if request.user:

            patient_obj = patient_user_object(request)
            if patient_obj:
                dashboard_details['patient'] = PatientSerializer(
                    patient_obj).data

            manipal_admin_obj = manipal_admin_object(request)
            if manipal_admin_obj:
                dashboard_details['manipal_admin'] = ManipalAdminSerializer(
                    manipal_admin_obj).data

        return Response(dashboard_details, status=status.HTTP_200_OK)
