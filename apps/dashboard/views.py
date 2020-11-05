from django.conf import settings
from django.db.models import Sum

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.appointments.serializers import AppointmentSerializer
from apps.doctors.models import Doctor
from apps.lab_and_radiology_items.models import (HomeCollectionAppointment,
                                                 PatientServiceAppointment)
from apps.manipal_admin.serializers import ManipalAdminSerializer
from apps.notifications.models import MobileDevice
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import PatientSerializer
from apps.payments.models import Payment
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from utils import custom_viewsets
from utils.custom_permissions import IsManipalAdminUser
from utils.utils import (get_appointment, manipal_admin_object,
                         patient_user_object)

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
                version_number = self.request.query_params.get("version", None)
                if version_number:
                    dashboard_details["force_update_enable"] = settings.FORCE_UPDATE_ENABLE
                    current_version = settings.IOS_VERSION
                    if version_number >= current_version:
                        dashboard_details["force_update_required"] = False
                    else:
                        dashboard_details["force_update_required"] = True

                dashboard_details['patient'] = PatientSerializer(
                    patient_obj).data
                patient_appointment = get_appointment(patient_obj.id)
                dashboard_details['upcoming_appointment'] = AppointmentSerializer(
                    patient_appointment, many=True
                ).data

            manipal_admin_obj = manipal_admin_object(request)
            if manipal_admin_obj:
                dashboard_details['manipal_admin'] = ManipalAdminSerializer(
                    manipal_admin_obj).data
                unique_uhid_info = set(Patient.objects.filter(
                    uhid_number__isnull=False).values_list('uhid_number', flat=True))
                unique_uhid_info.update(set(FamilyMember.objects.filter(
                    uhid_number__isnull=False, is_visible=True).values_list('uhid_number', flat=True)))
                dashboard_details['patients_count'] = len(unique_uhid_info)
                dashboard_details['app_users_count'] = Patient.objects.count()

                dashboard_details['registered_user_count'] = Patient.objects.filter(
                    mobile_verified=True).count()

                dashboard_details['user_with_uhid_count'] = Patient.objects.filter(
                    mobile_verified=True, uhid_number__isnull=False).count()

                dashboard_details['family_Member_count'] = FamilyMember.objects.filter(
                    is_visible=True).count()

                dashboard_details['family_Member_with_uhid_count'] = FamilyMember.objects.filter(
                    is_visible=True, uhid_number__isnull=False).count()

                dashboard_details["android_user"] = MobileDevice.objects.filter(
                    platform='Android').count()

                dashboard_details["apple_user"] = MobileDevice.objects.filter(
                    platform='iOS').count()

                dashboard_details['payments_info'] = {}
                dashboard_details['payments_info']["total"] = Payment.objects.filter(
                    status="success").count()
                dashboard_details['payments_info']["uhid_registration"] = Payment.objects.filter(
                    payment_for_uhid_creation=True, status="success").count()
                dashboard_details['payments_info']["uhid_total_amount"] = Payment.objects.filter(
                    payment_for_uhid_creation=True, status="success").aggregate(Sum('amount'))

                dashboard_details['payments_info']["doctor_consultation"] = Payment.objects.filter(
                    appointment__isnull=False, status="success").count()
                dashboard_details['payments_info']["doctor_consultation_total_amount"] = Payment.objects.filter(
                    appointment__isnull=False, status="success").aggregate(Sum('amount'))

                dashboard_details['payments_info']["health_package_count"] = Payment.objects.filter(
                    payment_for_health_package=True, status="success").count()
                dashboard_details['payments_info']["health_package_total_amount"] = Payment.objects.filter(
                    payment_for_health_package=True, status="success").aggregate(Sum('amount'))

                dashboard_details['payments_info']["inpatient_deposit_count"] = Payment.objects.filter(
                    payment_for_ip_deposit=True, status="success").count()
                dashboard_details['payments_info']["inpatient_deposit_total_amount"] = Payment.objects.filter(
                    payment_for_ip_deposit=True, status="success").aggregate(Sum('amount'))

                dashboard_details['payments_info']["payment_for_op_billing_count"] = Payment.objects.filter(
                    payment_for_op_billing=True, status="success").count()
                dashboard_details['payments_info']["payment_for_op_billing_total_amount"] = Payment.objects.filter(
                    payment_for_op_billing=True, status="success").aggregate(Sum('amount'))

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
                dashboard_details['appointment_statistics']['total'] = Appointment.objects.filter(
                    booked_via_app=True).count()
                dashboard_details['appointment_statistics']['confirmed'] = Appointment.objects.filter(
                    booked_via_app=True, status=1).count()
                dashboard_details['appointment_statistics']['cancelled'] = Appointment.objects.filter(
                    booked_via_app=True, status=2).count()

                dashboard_details['appointment_statistics']["video_consultation"] = Appointment.objects.filter(
                    booked_via_app=True, status=1, appointment_mode="VC", payment_status="success").count()

                dashboard_details['appointment_statistics']["opd_visit"] = Appointment.objects.filter(
                    booked_via_app=True, status=1, appointment_mode="HV").count()

                dashboard_details['appointment_statistics']["rescheduled"] = Appointment.objects.filter(
                    booked_via_app=True, status=5).count()

                dashboard_details['appointment_statistics']['total_appointment_hospital_wise'] = Appointment.objects.filter(
                    status=1, booked_via_app=True).values('hospital__code').annotate(Count('hospital'))

                dashboard_details['appointment_statistics']['opd_appointment_hospital_wise'] = Appointment.objects.filter(
                    booked_via_app=True, status=1, appointment_mode="HV").values('hospital__code').annotate(Count('hospital'))

                dashboard_details['appointment_statistics']['vc_appointment_hospital_wise'] = Appointment.objects.filter(
                    booked_via_app=True, status=1, appointment_mode="VC", payment_status="success").values('hospital__code').annotate(Count('hospital'))

                dashboard_details['health_package_statistics'] = {}
                dashboard_details['health_package_statistics']['total'] = HealthPackageAppointment.objects.filter(
                    payment_id__status="success").count()
                dashboard_details['health_package_statistics']['booked'] = HealthPackageAppointment.objects.filter(
                    payment_id__status="success", appointment_status="Booked").count()
                dashboard_details['health_package_statistics']['Cancelled'] = HealthPackageAppointment.objects.filter(
                    payment_id__status="success", appointment_status="Cancelled").count()
                dashboard_details['health_package_statistics']['Not_Booked'] = HealthPackageAppointment.objects.filter(
                    payment_id__status="success", appointment_status="Not Booked").count()

        return Response(dashboard_details, status=status.HTTP_200_OK)
