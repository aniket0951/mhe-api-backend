from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.doctors.models import Doctor
from apps.lab_and_radiology_items.models import (HomeCollectionAppointment,
                                                 PatientServiceAppointment)
from apps.manipal_admin.serializers import ManipalAdminSerializer
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import PatientSerializer
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
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
                unique_uhid_info = set(Patient.objects.filter(
                    uhid_number__isnull=False).values_list('uhid_number', flat=True))
                unique_uhid_info.update(set(FamilyMember.objects.filter(
                    uhid_number__isnull=False).values_list('uhid_number', flat=True)))
                dashboard_details['patients_count'] = len(unique_uhid_info)
                dashboard_details['app_users_count'] = Patient.objects.count()

                dashboard_details['home_collection_statistics'] = {}
                dashboard_details['home_collection_statistics']['total'] = HomeCollectionAppointment.objects.count(
                )
                dashboard_details['home_collection_statistics']['pending'] = HomeCollectionAppointment.objects.filter(
                    status='Pending').count()
                dashboard_details['home_collection_statistics']['completed'] = HomeCollectionAppointment.objects.filter(
                    status='Completed').count()
                dashboard_details['home_collection_statistics']['in_progress'] = HomeCollectionAppointment.objects.filter(
                    status='In Progress').count()
                dashboard_details['home_collection_statistics']['cancelled'] = HomeCollectionAppointment.objects.filter(
                    status='Cancelled').count()

                dashboard_details['services_statistics'] = {}
                dashboard_details['services_statistics']['total'] = PatientServiceAppointment.objects.count(
                )
                dashboard_details['services_statistics']['pending'] = PatientServiceAppointment.objects.filter(
                    status='Pending').count()
                dashboard_details['services_statistics']['completed'] = PatientServiceAppointment.objects.filter(
                    status='Completed').count()
                dashboard_details['services_statistics']['in_progress'] = PatientServiceAppointment.objects.filter(
                    status='In Progress').count()
                dashboard_details['services_statistics']['cancelled'] = PatientServiceAppointment.objects.filter(
                    status='Cancelled').count()

                dashboard_details['doctor_count'] = Doctor.objects.count()

                dashboard_details['appointment_statistics'] = {}
                dashboard_details['appointment_statistics']['total'] = Appointment.objects.count(
                )
                dashboard_details['appointment_statistics']['confirmed'] = Appointment.objects.filter(
                    status=1).count()
                dashboard_details['appointment_statistics']['cancelled'] = Appointment.objects.filter(
                    status=2).count()

                dashboard_details['health_package_statistics'] = {}
                dashboard_details['health_package_statistics']['total'] = HealthPackageAppointment.objects.filter(
                    payment_id__status="success").count()
                dashboard_details['health_package_statistics']['booked'] = HealthPackageAppointment.objects.filter(
                    payment_id__status="success", appointment_status="Booked").count()

        return Response(dashboard_details, status=status.HTTP_200_OK)
