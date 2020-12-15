from django.conf import settings
from django.db.models import Count, Sum

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.appointments.serializers import AppointmentSerializer
from apps.doctors.models import Doctor
from apps.lab_and_radiology_items.models import (HomeCollectionAppointment,
                                                 PatientServiceAppointment)
from apps.manipal_admin.serializers import ManipalAdminSerializer
from apps.manipal_admin.models import ManipalAdmin
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
                    uhid_number__isnull=False, mobile_verified=True).values_list('uhid_number', flat=True))
                unique_uhid_info.update(set(FamilyMember.objects.filter(
                    uhid_number__isnull=False, is_visible=True).values_list('uhid_number', flat=True)))
                dashboard_details['patients_count'] = len(unique_uhid_info)

                user_without_uhid_count = Patient.objects.filter(
                    uhid_number__isnull=True, mobile_verified=True).count() + FamilyMember.objects.filter(
                    uhid_number__isnull=True, is_visible=True).count()
                dashboard_details['app_users_count'] = dashboard_details['patients_count'] + \
                    user_without_uhid_count

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

                payment_qs = Payment.objects.all()
                appointment_qs = Appointment.objects.all()
                home_collection_qs = HomeCollectionAppointment.objects.all()
                patient_service_qs = PatientServiceAppointment.objects.all()
                health_package_qs = HealthPackageAppointment.objects.all()

                if request.query_params.get("filter"):
                    date_from = self.request.query_params.get(
                        "date_from", None)
                    date_to = self.request.query_params.get("date_to", None)
                    if date_from and date_to:
                        payment_qs = Payment.objects.filter(
                            created_at__date__range=[date_from, date_to])
                        appointment_qs = Appointment.objects.filter(
                            created_at__date__range=[date_from, date_to])
                        home_collection_qs = HomeCollectionAppointment.objects.filter(
                            created_at__date__range=[date_from, date_to])
                        patient_service_qs = PatientServiceAppointment.objects.filter(
                            created_at__date__range=[date_from, date_to])
                        health_package_qs = HealthPackageAppointment.objects.filter(
                            created_at__date__range=[date_from, date_to])

                    location_code = self.request.query_params.get(
                        "location_code", None)

                    if location_code:
                        payment_qs = payment_qs.filter(
                            location__code=location_code)
                        appointment_qs = appointment_qs.filter(
                            hospital__code=location_code)
                        home_collection_qs = home_collection_qs.filter(
                            hospital__code=location_code)
                        patient_service_qs = patient_service_qs.filter(
                            hospital__code=location_code)
                        health_package_qs = health_package_qs.filter(
                            hospital__code=location_code)

                dashboard_details['payments_info'] = {}
                dashboard_details['payments_info']["total"] = payment_qs.filter(
                    status="success").count()
                dashboard_details['payments_info']["uhid_registration"] = payment_qs.filter(
                    payment_for_uhid_creation=True, status="success").count()
                dashboard_details['payments_info']["uhid_total_amount"] = payment_qs.filter(
                    payment_for_uhid_creation=True, status="success").aggregate(Sum('amount'))

                dashboard_details['payments_info']["doctor_consultation"] = payment_qs.filter(
                    appointment__isnull=False, status="success").count()
                dashboard_details['payments_info']["doctor_consultation_total_amount"] = payment_qs.filter(
                    appointment__isnull=False, status="success").aggregate(Sum('amount'))

                dashboard_details['payments_info']["health_package_count"] = payment_qs.filter(
                    payment_for_health_package=True, status="success").count()
                dashboard_details['payments_info']["health_package_total_amount"] = payment_qs.filter(
                    payment_for_health_package=True, status="success").aggregate(Sum('amount'))

                dashboard_details['payments_info']["inpatient_deposit_count"] = payment_qs.filter(
                    payment_for_ip_deposit=True, status="success").count()
                dashboard_details['payments_info']["inpatient_deposit_total_amount"] = payment_qs.filter(
                    payment_for_ip_deposit=True, status="success").aggregate(Sum('amount'))

                dashboard_details['payments_info']["payment_for_op_billing_count"] = payment_qs.filter(
                    payment_for_op_billing=True, status="success").count()
                dashboard_details['payments_info']["payment_for_op_billing_total_amount"] = payment_qs.filter(
                    payment_for_op_billing=True, status="success").aggregate(Sum('amount'))

                dashboard_details['home_collection_statistics'] = {}
                dashboard_details['home_collection_statistics']['total'] = home_collection_qs.count(
                )
                dashboard_details['home_collection_statistics']['pending'] = home_collection_qs.filter(
                    status='Pending').count()
                dashboard_details['home_collection_statistics']['completed'] = home_collection_qs.filter(
                    status='Completed').count()
                dashboard_details['home_collection_statistics']['in_progress'] = home_collection_qs.filter(
                    status='In Progress').count()
                dashboard_details['home_collection_statistics']['cancelled'] = home_collection_qs.filter(
                    status='Cancelled').count()

                dashboard_details['services_statistics'] = {}
                dashboard_details['services_statistics']['total'] = patient_service_qs.count(
                )
                dashboard_details['services_statistics']['pending'] = patient_service_qs.filter(
                    status='Pending').count()
                dashboard_details['services_statistics']['completed'] = patient_service_qs.filter(
                    status='Completed').count()
                dashboard_details['services_statistics']['in_progress'] = patient_service_qs.filter(
                    status='In Progress').count()
                dashboard_details['services_statistics']['cancelled'] = patient_service_qs.filter(
                    status='Cancelled').count()

                dashboard_details['doctor_count'] = Doctor.objects.count()

                dashboard_details['appointment_statistics'] = {}
                dashboard_details['appointment_statistics']['total'] = appointment_qs.filter(
                    booked_via_app=True).count()
                dashboard_details['appointment_statistics']['confirmed'] = appointment_qs.filter(
                    booked_via_app=True, status=1).count()
                dashboard_details['appointment_statistics']['cancelled'] = appointment_qs.filter(
                    booked_via_app=True, status=2).count()

                dashboard_details['appointment_statistics']["video_consultation"] = appointment_qs.filter(
                    booked_via_app=True, status=1, appointment_mode="VC", payment_status="success").count()

                dashboard_details['appointment_statistics']["opd_visit"] = appointment_qs.filter(
                    booked_via_app=True, status=1, appointment_mode="HV").count()

                dashboard_details['appointment_statistics']["rescheduled"] = appointment_qs.filter(
                    booked_via_app=True, status=5).count()

                dashboard_details['appointment_statistics']['total_appointment_hospital_wise'] = list(appointment_qs.filter(
                    status=1, booked_via_app=True).values('hospital__code').annotate(Count('hospital')))

                dashboard_details['appointment_statistics']['opd_appointment_hospital_wise'] = list(appointment_qs.filter(
                    booked_via_app=True, status=1, appointment_mode="HV").values('hospital__code').annotate(Count('hospital')))

                dashboard_details['appointment_statistics']['vc_appointment_hospital_wise'] =  list(appointment_qs.filter(
                    booked_via_app=True, status=1, appointment_mode="VC", payment_status="success").values('hospital__code').annotate(Count('hospital')))

                dashboard_details['health_package_statistics'] = {}
                dashboard_details['health_package_statistics']['total'] = health_package_qs.filter(
                    payment_id__status="success").count()
                dashboard_details['health_package_statistics']['booked'] = health_package_qs.filter(
                    payment_id__status="success", appointment_status="Booked").count()
                dashboard_details['health_package_statistics']['Cancelled'] = health_package_qs.filter(
                    payment_id__status="success", appointment_status="Cancelled").count()
                dashboard_details['health_package_statistics']['Not_Booked'] = health_package_qs.filter(
                    payment_id__status="success", appointment_status="Not Booked").count()

        return Response(dashboard_details, status=status.HTTP_200_OK)
