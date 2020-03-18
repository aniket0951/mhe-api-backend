from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.manipal_admin.serializers import ManipalAdminSerializer
from apps.patients.models import FamilyMember, Patient
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
                unique_uhid_info = set(Patient.objects.filter(uhid_number__isnull=False).values_list('uhid_number', flat=True))
                unique_uhid_info.update(set(FamilyMember.objects.filter(uhid_number__isnull=False).values_list('uhid_number', flat=True)))
                dashboard_details['patients_count'] = len(unique_uhid_info)
                dashboard_details['app_users_count'] = Patient.objects.count()
            
        return Response(dashboard_details, status=status.HTTP_200_OK)
