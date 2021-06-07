import base64
from datetime import date, datetime
from apps.appointments import models
from apps.dashboard.constants import DashboardConstants
from apps.master_data.models import Configurations
from apps.master_data.serializers import ComponentsSerializer, ConfigurationSerializer
from django.conf import settings
from django.db.models import Count, Sum

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
from rest_framework import status, filters
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from utils import custom_viewsets
from utils.custom_permissions import BlacklistUpdateMethodPermission, IsManipalAdminUser, IsPatientUser, BlacklistDestroyMethodPermission
from utils.utils import (
                    get_appointment, 
                    manipal_admin_object,
                    patient_user_object
                )
from .models import DashboardBanner, FAQData, FlyerImages, FlyerScheduler
from .serializers import DashboardBannerSerializer, FAQDataSerializer, FlyerImagesSerializer, FlyerSchedulerSerializer
from .utils import DashboardUtils
import logging
from django_filters.rest_framework import DjangoFilterBackend

_logger = logging.getLogger("Django")

class DashboardBannerViewSet(custom_viewsets.CreateDeleteViewSet):
    permission_classes = [IsManipalAdminUser]
    model = DashboardBanner
    queryset = DashboardBanner.objects.all()
    serializer_class = DashboardBannerSerializer
    create_success_message = "New dashboard banner added successfully."
    delete_success_message = "Dashboard banner deleted successfully."

class IOSVersionCheck(ListAPIView):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        dashboard_details = {}
        version_number = self.request.query_params.get("version", None)
        dashboard_details = DashboardUtils.validate_app_version(version_number,dashboard_details)
        
        return Response(dashboard_details, status=status.HTTP_200_OK)

class DashboardAPIView(ListAPIView):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):

        dashboard_details = {}
        dashboard_details['banners'] = DashboardBannerSerializer(DashboardBanner.objects.all(), many=True).data
        dashboard_details['configurations'] = ConfigurationSerializer(Configurations.objects.filter(allowed_components__is_active=True).first(),many=False).data

        version_number = self.request.query_params.get("version", None)
        dashboard_details = DashboardUtils.validate_app_version(version_number,dashboard_details)
        
        if request.user:

            patient_obj = patient_user_object(request)
            if patient_obj:

                if  patient_obj.active_view == 'Corporate' and \
                    dashboard_details['configurations'].get("allowed_components") and \
                    patient_obj.company_info and \
                    patient_obj.company_info.component_ids:
                    dashboard_details['configurations']["allowed_components"] = ComponentsSerializer(patient_obj.company_info.component_ids,many=True).data

                dashboard_details['patient'] = PatientSerializer(patient_obj).data
                patient_appointment = get_appointment(patient_obj.id)
                dashboard_details['upcoming_appointment'] = AppointmentSerializer(patient_appointment, many=True).data
                dashboard_details["vaccination_age_error_message"] = settings.VACCINATION_AGE_ERROR_MESSAGE.format(str(settings.MIN_VACCINATION_AGE))
                dashboard_details['manipal_whatsapp_contact'] = settings.MANIPAL_WHATSAPP_CONTACT
                if settings.FLYER_ENABLED:
                    dashboard_details['flyers_images'] = DashboardUtils.get_all_todays_flyers()

            manipal_admin_obj = manipal_admin_object(request)
            if manipal_admin_obj:

                dashboard_details['manipal_admin'] = ManipalAdminSerializer(manipal_admin_obj).data

                patients_with_uhid = set(Patient.objects.filter(uhid_number__isnull=False, mobile_verified=True).values_list('uhid_number', flat=True))
                family_members_with_uhid = set(FamilyMember.objects.filter(uhid_number__isnull=False, is_visible=True).values_list('uhid_number', flat=True))

                unique_uhid_info = patients_with_uhid.copy()
                unique_uhid_info.update(family_members_with_uhid.copy())
                user_with_uhid_count = len(unique_uhid_info)

                patients_without_uhid = Patient.objects.filter(uhid_number__isnull=True, mobile_verified=True).count()
                family_members_without_uhid = FamilyMember.objects.filter(uhid_number__isnull=True, is_visible=True).count()
                user_without_uhid_count = patients_without_uhid + family_members_without_uhid

                app_users_count = user_with_uhid_count + user_without_uhid_count

                dashboard_details['patients_count'] = user_with_uhid_count

                dashboard_details['user_with_uhid_count'] = len(patients_with_uhid)
                dashboard_details['family_Member_with_uhid_count'] = len(family_members_with_uhid)

                dashboard_details['app_users_count'] = app_users_count

                dashboard_details['registered_user_count'] = Patient.objects.filter(mobile_verified=True).count()

                dashboard_details['family_Member_count'] = FamilyMember.objects.filter(is_visible=True).count()

                dashboard_details["android_user"] = MobileDevice.objects.filter(platform='Android').count()

                dashboard_details["apple_user"] = MobileDevice.objects.filter(platform='iOS').count()

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

class FAQDataViewSet(custom_viewsets.CreateDeleteViewSet):
    permission_classes = [IsManipalAdminUser]
    model = FAQData
    queryset = FAQData.objects.all()
    serializer_class = FAQDataSerializer
    create_success_message = "New FAQ data added successfully."
    delete_success_message = "FAQ data deleted successfully."

class FAQDataAPIView(ListAPIView):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        faq_data_details = {
            FAQData.BANNER:[],
            FAQData.DESCRIPTION:[],
            FAQData.QNA:[],
            FAQData.VIDEO:[]
        }
        faq_data = FAQDataSerializer(FAQData.objects.order_by('code').all(), many=True).data
        if faq_data:
            for faq in faq_data:
                faq_data_details[faq["type"]].append(faq)
        
        return Response(faq_data_details, status=status.HTTP_200_OK)
    
class RemoveAccountAPIView(ListAPIView):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        contact_number = self.request.query_params.get("contact_number", None)
        if not contact_number:
            return Response({"error":"Please provide 10 digit contact_number"}, status=status.HTTP_400_BAD_REQUEST)
        if not settings.DELETE_ACCOUNT_API:
            return Response({"error":"This feature is not enabled!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            contact_number = int(contact_number)
            patient = Patient.objects.filter(mobile=DashboardConstants.MOBILE_NUMBER_PREFIX%(str(contact_number))).first()
            if not patient:
                return Response({"error":"No patient found for the given number!"}, status=status.HTTP_400_BAD_REQUEST)
            contact_number+=1
            while (Patient.objects.filter(mobile=DashboardConstants.MOBILE_NUMBER_PREFIX%(str(contact_number))).first()):
                contact_number+=1
            patient.mobile = DashboardConstants.MOBILE_NUMBER_PREFIX%(str(contact_number))
            patient.save()
        except Exception as e:
            _logger.error("Exception in RemoveAccountAPIView: %s"%(str(e)))
            return Response({"error":"Invalid contact number provided!"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message":"Your number has been deleted successfully!"}, status=status.HTTP_200_OK)

class RemoveUHIDAPIView(ListAPIView):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        uhid_number = self.request.query_params.get("uhid_number", None)
        if not uhid_number:
            return Response({"error":"Please provide uhid_number"}, status=status.HTTP_400_BAD_REQUEST)
        if not settings.DELETE_ACCOUNT_API:
            return Response({"error":"This feature is not enabled!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            patient = Patient.objects.filter(uhid_number="%s"%(str(uhid_number).upper())).first()
            if not patient:
                return Response({"error":"No patient found for the given uhid_number!"}, status=status.HTTP_400_BAD_REQUEST)
            patient.uhid_number = None
            patient.save()
        except Exception as e:
            _logger.error("Exception in RemoveUHIDAPIView: %s"%(str(e)))
            return Response({"error":"Invalid uhid_number provided!"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message":"Your uhid_number has been unlinked successfully!"}, status=status.HTTP_200_OK)


class FlyerImagesViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser]
    model = FlyerImages
    queryset = FlyerImages.objects.all()
    serializer_class = FlyerImagesSerializer
    create_success_message = "Flyer image added successfully!"
    list_success_message = 'Flyer images returned successfully!'
    retrieve_success_message = 'Flyer image returned successfully!'
    update_success_message = 'Flyer image updated successfully!'
    delete_success_message = 'Flyer image deleted successfully!'
    
    def perform_create(self, serializer):
        flyer_scheduler_id = self.request.data.get('flyer_scheduler_id')
        sequence = self.request.data.get('sequence')        
        DashboardUtils.validate_flyers_sequence(flyer_scheduler_id,sequence)
        DashboardUtils.validate_max_no_of_flyers(flyer_scheduler_id)
        serializer.save()
        
    def perform_update(self, serializer):
        if 'sequence' in self.request.data and 'flyer_scheduler_id' in self.request.data:
            flyer_scheduler_id = self.request.data.get('flyer_scheduler_id') 
            sequence = self.request.data.get('sequence')
            flyer_image_object = self.get_object()
            DashboardUtils.validate_flyers_sequence(flyer_scheduler_id,sequence,flyer_image_object.id)
        serializer.save() 

class FlyerSchedulerViewSet(custom_viewsets.CreateUpdateListRetrieveModelViewSet):
    permission_classes = [IsPatientUser | IsManipalAdminUser]
    queryset = FlyerScheduler.objects.all().order_by('-start_date_time','-end_date_time','-created_at')
    model = FlyerScheduler
    serializer_class = FlyerSchedulerSerializer
    create_success_message = "Flyer schedulers added successfully!"
    list_success_message = 'Flyer schedulers returned successfully!'
    retrieve_success_message = 'Flyer scheduler returned successfully!'
    update_success_message = 'Flyer schedulers updated successfully!'
    delete_success_message = 'Flyer schedulers deleted successfully!'
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    search_fields = ('flyer_name','start_date_time','end_date_time',)
    
    def get_permissions(self):

        if self.action in ['create','partial_update']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPatientUser | IsManipalAdminUser]
            return [permission() for permission in permission_classes]
        
        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        date_from = self.request.query_params.get("date_from", None)
        date_to = self.request.query_params.get("date_to", None)
        if date_from and date_to:
            qs = qs.filter(start_date_time__date__range=[date_from, date_to],end_date_time__date__range=[date_from,date_to])
        return qs
    
    def perform_create(self, serializer):
        current_date = date.today()

        start_date_time = self.request.data.get('start_date_time')
        end_date_time = self.request.data.get('end_date_time')
        
        if 'start_date_time' in self.request.data:
            start_datetime = datetime.strptime(start_date_time,'%Y-%m-%dT%H:%M:%S')
            if start_datetime.date() < current_date:
                raise ValidationError('Start date time should not be set as past date.')

            if 'end_date_time' in self.request.data:
                DashboardUtils.start_end_datetime_comparision(start_date_time,end_date_time)

        serializer.save(is_active=True)

    def perform_update(self, serializer):
        if 'start_date_time' in self.request.data and 'end_date_time' in self.request.data:
            start_date_time = self.request.data.get('start_date_time')
            end_date_time = self.request.data.get('end_date_time')

            DashboardUtils.start_end_datetime_comparision(start_date_time,end_date_time)
            
        serializer.save()