import json
import logging
import xml.etree.ElementTree as ET
from datetime import timedelta

from django.contrib.gis.db.models.functions import Distance as Django_Distance
from django.contrib.gis.geos import Point
from django.db.models import Q
from django.utils.timezone import datetime
from django.conf import settings

from apps.doctors.exceptions import DoctorDoesNotExistsValidationException
from apps.doctors.models import Doctor
from apps.health_packages.models import HealthPackage, HealthPackagePricing
from apps.health_packages.serializers import (HealthPackage, HealthPackagePricing)
from apps.health_tests.models import HealthTest
from apps.lab_and_radiology_items.models import (LabRadiologyItem, LabRadiologyItemPricing)
from apps.patients.serializers import PatientSerializer,FamilyMemberSerializer
from apps.notifications.tasks import (daily_update_scheduler, update_doctor,
                                      update_health_package, update_item)
from apps.master_data.utils import MasterDataUtils
from apps.patients.models import FamilyMember, Patient
from apps.master_data.constants import MasterDataConstants
from apps.appointments.models import Appointment

from utils.utils import check_code

from proxy.custom_endpoints import SYNC_SERVICE, VALIDATE_OTP, VALIDATE_UHID
from proxy.custom_serializables import \
    ItemTariffPrice as serializable_ItemTariffPrice
from proxy.custom_serializables import LinkUhid as serializable_LinkUhid
from proxy.custom_serializables import \
    PatientAppStatus as serializable_patient_app_status
from proxy.custom_serializables import \
    UhidBasedConsultation as serializable_uhid_based_consultation
from proxy.custom_serializables import \
    ValidatePatientMobile as serializable_validate_patient_mobile
from proxy.custom_serializables import \
    ValidateUHID as serializable_validate_UHID
from proxy.custom_serializables import \
    PatientDetails as serializable_patient_details_by_mobile    
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView

from rest_framework import filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend

from utils import custom_viewsets
from utils.custom_permissions import (BlacklistDestroyMethodPermission,
                                      BlacklistUpdateMethodPermission,
                                      InternalAPICall,
                                      IsManipalAdminUser,
                                      BlacklistCreateMethodPermission,
                                      IsPatientUser
                                     )
                                     
from utils.utils import get_report_info,patient_user_object
from utils.send_invite import send_appointment_invitation

from .exceptions import (DoctorHospitalCodeMissingValidationException,
                         HospitalCodeMissingValidationException,
                         HospitalDoesNotExistsValidationException,
                         InvalidHospitalCodeValidationException,
                         ItemOrDepartmentDoesNotExistsValidationException)
from .models import (AmbulanceContact, BillingGroup, BillingSubGroup, Company,
                     Department, EmergencyContact, FeedbackRecipients, HelplineNumbers, Hospital,
                     HospitalDepartment, Specialisation, Components, CompanyDomain, Configurations, Medicine, Billing)
from .serializers import (AmbulanceContactSerializer, CompanySerializer,
                          DepartmentSerializer, EmergencyContactSerializer, FeedbackRecipientSerializer, HelplineNumbersSerializer,
                          HospitalDepartmentSerializer, HospitalSerializer,
                          HospitalSpecificSerializer, SpecialisationSerializer,ComponentsSerializer, CompanyDomainsSerializer, ConfigurationSerializer, MedicineSerializer,BillingSerializer)

logger = logging.getLogger('django')


class HospitalViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    model = Hospital
    queryset = Hospital.objects.all().order_by('-created_at')
    serializer_class = HospitalSerializer
    create_success_message = 'Hospital information created successfully!'
    list_success_message = 'Hospitals list returned successfully!'
    retrieve_success_message = 'Hospital information returned successfully!'
    update_success_message = 'Hospital information updated successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['code', 'description', 'address', ]
    filter_fields = ['is_home_collection_supported', ]
    ordering_fields = ('code',)

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['update', 'partial_update', 'create']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]
        return super().get_permissions()

    def get_queryset(self):
        try:
            qs = super().get_queryset().filter(hospital_enabled=True)
            longitude = float(self.request.query_params.get("longitude", 0))
            latitude = float(self.request.query_params.get("latitude", 0))
            corporate = self.request.query_params.get("corporate", None)
            if longitude and latitude:
                user_location = Point(longitude, latitude, srid=4326)
                if corporate:
                    company_id = self.request.query_params.get(
                        "company_id", None)
                    company = Company.objects.filter(id=company_id).first()
                    if company:
                        qs = company.hospital_info.all()
                        return qs.annotate(calculated_distance=Django_Distance('location', user_location)).order_by('calculated_distance')
                qs = qs.filter(corporate_only=False)
                return qs.annotate(calculated_distance=Django_Distance('location', user_location)).order_by('calculated_distance')
        except Exception as e:
            logger.info("Exception in HospitalViewSet: %s"%(str(e)))
        return super().get_queryset()

    def post(self, request, format=None):
        longitude = float(self.request.data.pop("longitude", 0))
        latitude = float(self.request.data.pop("latitude", 0))
        mobile = self.request.data.pop("ambulance_contact_number", None)
        if not (longitude and latitude):
            raise ValidationError("Mandatory Parameter missing")
        location = Point(longitude, latitude, srid=4326)
        self.request.data["location"] = location
        hospital_serializer = HospitalSpecificSerializer(
            data=self.request.data)
        hospital_serializer.is_valid(raise_exception=True)
        hospital_instance = hospital_serializer.save()
        ambulance_data = dict()
        ambulance_data["mobile"] = mobile
        ambulance_data["hospital"] = hospital_instance
        try:
            contact, contact_created = AmbulanceContact.objects.update_or_create(
                **ambulance_data, defaults=ambulance_data)
        except Exception as error:
            logger.error("Exception in HospitalViewSet: %s"%(str(error)))
        return Response(data=hospital_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def update_hospital_location(self, request):
        hospital_id = self.request.data.get("hospital_id")
        longitude = float(self.request.data.get("longitude", 0))
        latitude = float(self.request.data.get("latitude", 0))
        hospital_instance = Hospital.objects.filter(id=hospital_id).first()
        if not (longitude and latitude and hospital_instance):
            raise ValidationError("Mandatory Parameter missing")
        location = Point(longitude, latitude, srid=4326)
        hospital_instance.location = location
        hospital_instance.save()
        return Response(data={"message": "Location Updated"}, status=status.HTTP_200_OK)


class HospitalDepartmentViewSet(custom_viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    model = HospitalDepartment
    queryset = HospitalDepartment.objects.all()
    serializer_class = HospitalDepartmentSerializer
    create_success_message = None
    list_success_message = 'Hospital departments list returned successfully!'
    retrieve_success_message = 'Hospital department information returned successfully!'
    update_success_message = None
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['department__code', 'department__name', 'hospital__code', 'hospital__description']
    filter_fields = ('hospital__id','service','sub_service')
    ordering = ('department_id__name')

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset().filter(
            (Q(end_date__gte=datetime.now().date()) | Q(end_date__isnull=True)) &
            Q(start_date__lte=datetime.now().date()))
        service = self.request.query_params.get("service", None)
        if patient_user_object(self.request) and not service:
            qs = qs.exclude(Q(service__in=[settings.COVID_SERVICE]))
        return qs

class SpecialisationViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = Specialisation
    queryset = Specialisation.objects.all()
    serializer_class = SpecialisationSerializer
    create_success_message = "New specialisation is added successfully."
    list_success_message = 'Specialisations list returned successfully!'
    retrieve_success_message = 'Specialisation information returned successfully!'
    update_success_message = 'Information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['code', 'description', ]
    ordering_fields = ('code',)

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'create']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        return super().get_queryset().filter(
            (Q(end_date__gte=datetime.now().date()) | Q(end_date__isnull=True)) &
            Q(start_date__lte=datetime.now().date()))


class DepartmentsView(ProxyView):
    permission_classes = [InternalAPICall]
    source = SYNC_SERVICE
    success_msg = 'Departments list returned successfully'
    sync_method = 'department'

    def get_request_data(self, request):
        return self.get_sync_request_data(request)

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        logger.info(response.content)
        root = ET.fromstring(response._content)
        item = root.find('SyncResponse')

        if item.text.startswith(MasterDataConstants.REQUEST_PARAM):
            raise HospitalCodeMissingValidationException
        try:
            response_content = json.loads(item.text)
        except Exception:
            raise InvalidHospitalCodeValidationException

        all_departments = list()
        department_sorted_keys = ['start_date',
                                  'end_date',
                                  'code',
                                  'name',
                                  'hospital_code',
                                  'service',
                                  'sub_service'
                                  ]
        for each_department in response_content:

            department_details = MasterDataUtils.process_department_details(each_department,department_sorted_keys)

            department_kwargs = dict()
            hospital_department_details = dict()
            hospital_department_kwargs = dict()
            hospital_code = department_details.pop('hospital_code')
            hospital_department_details['start_date'] = department_details.pop('start_date')
            hospital_department_details['end_date'] = department_details.pop('end_date')

            service = department_details.pop('service')
            hospital_department_details['service'] = service.lower() if service else ""
            sub_service = department_details.pop('sub_service')
            hospital_department_details['sub_service'] = sub_service.lower() if sub_service else ""

            hospital = Hospital.objects.filter(code=hospital_code).first()

            department_kwargs['code'] = department_details['code']
            department, department_created = Department.objects.update_or_create(**department_kwargs,defaults=department_details)

            department_details['department_created'] = department_created

            hospital_department_kwargs['hospital'] = hospital
            hospital_department_kwargs['department'] = department
            hospital_department_details.update(hospital_department_kwargs)

            _, hospital_department_created = HospitalDepartment.objects.update_or_create(
                                                            **hospital_department_kwargs, 
                                                            defaults=hospital_department_details
                                                        )
            department_details['hospital_department_created'] = hospital_department_created

            all_departments.append(department_details)

            today_date = datetime.now().date()
            previous_date = datetime.now() - timedelta(days=1)
            HospitalDepartment.objects.filter(
                                    updated_at__date__lt=today_date, 
                                    end_date__isnull=True
                                ).update(end_date=previous_date.date())

        return self.custom_success_response(
                                    message=self.success_msg,
                                    success=True, 
                                    data=all_departments
                                )


class DoctorsView(ProxyView):
    permission_classes = [InternalAPICall]

    source = SYNC_SERVICE
    success_msg = 'Doctors list returned successfully'
    sync_method = 'doctor'

    def get_request_data(self, request):
        return self.get_sync_request_data(request)

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        logger.info(response.content)
        root = ET.fromstring(response._content)
        item = root.find('SyncResponse')
        if item.text.startswith(MasterDataConstants.REQUEST_PARAM):
            raise DoctorHospitalCodeMissingValidationException

        try:
            response_content = json.loads(item.text.replace(" \\ "," \\\\ "))
        except Exception as error:
            logger.error("Exception in DoctorsView: %s"%(str(error)))
            raise DoctorDoesNotExistsValidationException

        if not response_content:
            raise InvalidHospitalCodeValidationException

        all_doctors = list()
        doctor_sorted_keys = [
            "AllowWebDisplay",
            'start_date',
            'end_date',
            'department_code',
            'department_name',
            'code',
            'educational_degrees',
            'name',
            'notes',
            'profile',
            'qualification',
            'hospital_code',
            'is_online_appointment_enable',
            'hv_consultation_charges',
            'pr_consultation_charges',
            'specialisation_code',
            'specialisation_description',
            'vc_consultation_charges'
        ]
        today_date = datetime.now().date()
        for each_doctor in response_content:
            doctor_details = dict()
            doctor_details["is_active"] = True
            for index, key in enumerate(sorted(each_doctor.keys())):

                if key in ['DocProfile', 'DeptName', 'SpecDesc',"AllowWebDisplay"]:
                    continue

                if not each_doctor[key]:
                    each_doctor[key] = None

                if key in ['DateFrom', 'DateTo'] and each_doctor[key]:
                    each_doctor[key] = datetime.strptime(
                        each_doctor[key], '%d/%m/%Y').strftime(MasterDataConstants.DATE_FORMAT)

                if key == "DocName" and each_doctor[key]:
                    each_doctor[key] = each_doctor[key].title()

                if key == "IsOnlineAppt" and each_doctor[key]:
                    if each_doctor[key] == "Yes":
                        each_doctor[key] = True
                    else:
                        each_doctor[key] = False
                doctor_details[doctor_sorted_keys[index]] = each_doctor[key]
            doctor_kwargs = dict()
            hospital_department_obj = None
            specialisation_obj = None
            hospital_code = doctor_details.pop('hospital_code')
            hospital = Hospital.objects.filter(code=hospital_code).first()
            doctor_kwargs['code'] = doctor_details.pop('code')
            doctor_kwargs['hospital'] = hospital
            department_code = doctor_details.pop('department_code')
            if department_code:
                hospital_department_obj = HospitalDepartment.objects.filter(
                    department__code=department_code, hospital=hospital).first()
            specialisation_code = doctor_details.pop('specialisation_code')
            if specialisation_code:
                specialisation_obj = Specialisation.objects.filter(
                    code=specialisation_code).first()

            is_doctor_updated = Doctor.objects.filter(
                             code=doctor_kwargs['code'],
                             hospital__code=hospital_code
                         ).exclude(updated_at__date__lt=today_date).first()

            doctor, doctor_created = Doctor.objects.update_or_create(
                **doctor_kwargs, defaults=doctor_details)
            doctor_details['doctor_created'] = doctor_created

            if not is_doctor_updated:
                doctor.hospital_departments.clear()
                doctor.specialisations.clear()

            if hospital_department_obj:
                doctor.hospital_departments.add(hospital_department_obj)
            if specialisation_obj:
                doctor.specialisations.add(specialisation_obj)
            all_doctors.append(doctor_details)

        previous_date = datetime.now() - timedelta(days=1)
        Doctor.objects.filter(hospital__code=hospital_code,
                              updated_at__date__lt=today_date, end_date__isnull=True).update(end_date=previous_date.date())

        return self.custom_success_response(message=self.success_msg,
                                            success=True, data=all_doctors)


class HealthPackagesView(ProxyView):
    permission_classes = [InternalAPICall]
    source = SYNC_SERVICE
    success_msg = 'Health Packages list returned successfully'
    sync_method = 'healthcheck'

    def get_request_data(self, request):
        return self.get_sync_request_data(request)

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        logger.info(response.content)
        root = ET.fromstring(response._content)
        item = root.find('SyncResponse')
        if item.text.startswith(MasterDataConstants.REQUEST_PARAM):
            raise HospitalCodeMissingValidationException
        try:
            response_content = json.loads(item.text, strict=False)
        except Exception:
            raise HospitalDoesNotExistsValidationException

        all_health_packages = list()
        health_packages_sorted_keys = [
            'age_from',
            'age_to',
            'benefits',
            'billing_group',
            'billing_subgroup',
            'start_date',
            'end_date',
            'description',
            'discount_percentage',
            'discount_start_date',
            'discount_end_date',
            'gender',
            'hospital_code',
            'item_code',
            'item_description',
            'code',
            'name',
            'price',
            'specialisation_name'
        ]
        for each_health_package in response_content:
            health_package_details = dict()
            for index, key in enumerate(sorted(each_health_package.keys())):
                if not each_health_package[key]:
                    each_health_package[key] = None

                if key == 'AgeFrom' and not each_health_package[key]:
                    each_health_package[key] = 0

                if key == 'AgeTo' and not each_health_package[key]:
                    each_health_package[key] = 120

                if key == 'Gender' and (not each_health_package[key] in ['Male', 'Female'] or not each_health_package[key]):
                    each_health_package[key] = 'Male and Female'

                if key in ['DateFrom', 'DateTo', 'DiscDateFrom', 'DiscDateTo'] and each_health_package[key]:
                    each_health_package[key] = datetime.strptime(
                        each_health_package[key], '%d/%m/%Y').strftime(MasterDataConstants.DATE_FORMAT)

                if key == 'PackageName' and each_health_package[key]:
                    each_health_package[key] = each_health_package[key].title()

                health_package_details[health_packages_sorted_keys[index]
                                       ] = each_health_package[key]

            health_package_kwargs = dict()
            hospital_health_package_details = dict()
            hospital_health_package_kwargs = dict()
            health_test_details = dict()
            health_test_kwargs = dict()
            health_test_details['billing_group'] = health_package_details.pop(
                'billing_group')
            health_test_details['billing_sub_group'] = health_package_details.pop(
                'billing_subgroup')
            health_test_details['description'] = health_package_details.pop(
                'item_description')
            health_test_kwargs['code'] = health_package_details.pop(
                'item_code')

            if health_test_details['billing_group']:
                health_test_details['billing_group'] = BillingGroup.objects.filter(
                    description=health_test_details['billing_group']).first()

            if health_test_details['billing_sub_group']:
                health_test_details['billing_sub_group'] = BillingSubGroup.objects.filter(
                    description=health_test_details['billing_sub_group']).first()

            health_test, health_test_created = HealthTest.objects.update_or_create(
                **health_test_kwargs, defaults=health_test_details)

            hospital_code = health_package_details.pop('hospital_code')
            hospital_health_package_details['start_date'] = health_package_details.pop(
                'start_date')
            hospital_health_package_details['end_date'] = health_package_details.pop(
                'end_date')
            hospital_health_package_details['price'] = health_package_details.pop(
                'price')
            hospital_health_package_details['discount_percentage'] = health_package_details.pop(
                'discount_percentage')
            hospital_health_package_details['discount_start_date'] = health_package_details.pop(
                'discount_start_date')
            hospital_health_package_details['discount_end_date'] = health_package_details.pop(
                'discount_end_date')

            hospital = Hospital.objects.filter(code=hospital_code).first()

            health_package_kwargs['code'] = health_package_details['code']

            specialisation_name = health_package_details.pop(
                'specialisation_name')
            if specialisation_name:
                health_package_details['specialisation'] = Specialisation.objects.filter(
                    description=specialisation_name).first()

            try:
                health_package, health_package_created = HealthPackage.objects.update_or_create(
                    **health_package_kwargs, defaults=health_package_details)
                health_package.included_health_tests.add(health_test)

                hospital_health_package_kwargs['hospital'] = hospital
                hospital_health_package_kwargs['health_package'] = health_package
                hospital_health_package_details.update(
                    hospital_health_package_kwargs)

                _, hospital_health_package_created = HealthPackagePricing.objects.update_or_create(
                    **hospital_health_package_kwargs, defaults=hospital_health_package_details)

                health_package_details['health_test_created'] = health_test_created
                health_package_details['health_package_created'] = health_package_created
                health_package_details['hospital_health_package_created'] = hospital_health_package_created

                all_health_packages.append(health_package_details)

            except Exception as e:
                logger.error("Exception while syncing health packages : %s"%(str(e)))
                logger.error("Exception Data : %s"%(str(each_health_package)))

        today_date = datetime.now().date()
        previous_date = datetime.now() - timedelta(days=1)
        HealthPackagePricing.objects.filter(hospital__code=hospital_code,
                                            updated_at__date__lt=today_date, end_date__isnull=True).update(end_date=previous_date.date())
        return self.custom_success_response(message=self.success_msg,
                                            success=True, data=response_content)


class LabRadiologyItemsView(ProxyView):
    permission_classes = [InternalAPICall]
    source = SYNC_SERVICE
    success_msg = 'Lab Radiology items list returned successfully'
    sync_method = 'labraditems'

    def get_request_data(self, request):
        return self.get_sync_request_data(request)

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        logger.info(response.content)
        item = ET.fromstring(response._content).find('SyncResponse')
        if item.text.startswith(MasterDataConstants.REQUEST_PARAM):
            raise HospitalCodeMissingValidationException
        try:
            response_content = json.loads(item.text)
        except Exception:
            raise HospitalDoesNotExistsValidationException

        all_lab_radiology_items = list()
        lab_radiology_items_sorted_keys = ['billing_group',
                                           'billing_subgroup',
                                           'start_date',
                                           'end_date',
                                           'hospital_code',
                                           'code',
                                           'description',
                                           'price',
                                           ]
        for each_lab_radiology_item in response_content:

            each_lab_radiology_item, hospital_lab_radiology_item_details = MasterDataUtils.process_lab_and_radiology_items(each_lab_radiology_item,lab_radiology_items_sorted_keys)

            lab_radiology_item_kwargs, lab_radiology_item_details, hospital_lab_radiology_item_kwargs = dict(), dict(), dict()
            lab_radiology_item_details['billing_group'] = hospital_lab_radiology_item_details.pop('billing_group')
            lab_radiology_item_details['billing_sub_group'] = hospital_lab_radiology_item_details.pop('billing_subgroup')
            lab_radiology_item_details['description'] = hospital_lab_radiology_item_details.pop('description')
            lab_radiology_item_kwargs['code'] = hospital_lab_radiology_item_details.pop('code')

            if lab_radiology_item_details['billing_group']:
                lab_radiology_item_details['billing_group'] = BillingGroup.objects.filter(description=lab_radiology_item_details['billing_group']).first()

            if lab_radiology_item_details['billing_sub_group']:
                lab_radiology_item_details['billing_sub_group'] = BillingSubGroup.objects.filter(description=lab_radiology_item_details['billing_sub_group']).first()

            lab_radiology_item, lab_radiology_item_created = LabRadiologyItem.objects.update_or_create(**lab_radiology_item_kwargs, defaults=lab_radiology_item_details)

            hospital_code = hospital_lab_radiology_item_details.pop('hospital_code')
            hospital = Hospital.objects.filter(code=hospital_code).first()

            hospital_lab_radiology_item_kwargs['item'] = lab_radiology_item
            hospital_lab_radiology_item_kwargs['hospital'] = hospital

            hospital_lab_radiology_item, hospital_lab_radiology_item_created = LabRadiologyItemPricing.objects.update_or_create(**hospital_lab_radiology_item_kwargs, defaults=hospital_lab_radiology_item_details)

            hospital_lab_radiology_item_details['hospital_lab_radiology_item_created'] = hospital_lab_radiology_item_created
            hospital_lab_radiology_item_details['lab_radiology_item_created'] = lab_radiology_item_created

            all_lab_radiology_items.append(hospital_lab_radiology_item_details)

        return self.custom_success_response(message=self.success_msg,
                                            success=True, data=all_lab_radiology_items)


class ItemsTarrifPriceView(ProxyView):
    permission_classes = [AllowAny]
    source = SYNC_SERVICE
    success_msg = 'Lab Radiology items list returned successfully'
    sync_method = 'tariff'

    def get_request_data(self, request):
        request.data['sync_method'] = self.sync_method
        item_tariff_prices = serializable_ItemTariffPrice(**request.data)
        request_data = custom_serializer().serialize(item_tariff_prices, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        item = root.find('SyncResponse')

        try:
            response_content = json.loads(item.text)
        except Exception:
            raise ItemOrDepartmentDoesNotExistsValidationException

        return self.custom_success_response(message=self.success_msg,
                                            success=True, data=response_content)


class ValidateUHIDView(ProxyView):
    permission_classes = [AllowAny]
    source = VALIDATE_UHID
    success_msg = 'One time password has been sent on your registered mobile.'

    def get_request_data(self, request):
        uhid = serializable_validate_UHID(**request.data)
        request_data = custom_serializer().serialize(uhid, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        item = root.find('ValidateResponse')
        response_content = json.loads(item.text)[0]
        success = str(response_content.get('Status')) == "Pass"
        message = str(response_content.get('Message'))
        return self.custom_success_response(success, message)


class ValidateOTPView(ProxyView):
    permission_classes = [AllowAny]
    source = VALIDATE_OTP
    success_msg = 'OTP validated successfully'

    def get_request_data(self, request):
        uhid_otp = serializable_validate_UHID(**request.data)
        request_data = custom_serializer().serialize(uhid_otp, 'XML')

        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)

        item = root.find('ValidateResponse')
        response_content = json.loads(item.text)[0]
        success = str(response_content.get('Status')) == "Pass"
        message = response_content.get('Message')
        if success and not message:
            message = self.success_msg
        return self.custom_success_response(success=success, message=message,
                                            data=response_content)


class AmbulanceContactViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser]
    model = AmbulanceContact
    queryset = AmbulanceContact.objects.all()
    serializer_class = AmbulanceContactSerializer
    list_success_message = 'Ambulance Contact list returned successfully!'
    retrieve_success_message = 'Ambulance Contact returned successfully!'
    update_success_message = 'Ambulance Contact updated successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    filter_fields = ('hospital__id',)

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]
        return super().get_permissions()

    def get_queryset(self):
        try:
            longitude = float(self.request.query_params.get("longitude", 0))
            latitude = float(self.request.query_params.get("latitude", 0))
            if longitude and latitude:
                user_location = Point(longitude, latitude, srid=4326)
                return self.get_queryset().annotate(calculated_distance=Django_Distance('hospital__location',
                                                                                        user_location)).order_by('calculated_distance')
        except Exception as e:
            logger.info("Exception in AmbulanceContactViewSet: %s"%(str(e)))
        return super().get_queryset().order_by('hospital__code')


class PatientAppointmentStatus(ProxyView):
    permission_classes = [AllowAny]
    source = 'PatAppStats_Save'

    def get_request_data(self, request):
        hospital_code = request.data.get("hospital_code")
        specific_date = None
        if request.data.get("specific_date"):
            specific_date = request.data.get("specific_date")
        param = get_report_info(hospital_code=hospital_code,specific_date=specific_date)
        request_param = serializable_patient_app_status(param)
        request_data = custom_serializer().serialize(request_param, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        response_message = "Report could not pushed"
        response_success = False
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            response_message = root.find("PatAppStatsResponse").text
            response_success = True
        return self.custom_success_response(message=response_message,
                                            success=response_success, data=None)


class CompanyViewSet(custom_viewsets.CreateUpdateListRetrieveModelViewSet):
    permission_classes = [IsManipalAdminUser]
    model = Company
    depth =1
    queryset = Company.objects.all().order_by('-created_at')
    serializer_class = CompanySerializer
    list_success_message = 'Company list returned successfully!'
    retrieve_success_message = 'Company returned successfully!'
    update_success_message = 'Company details updated successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    ordering_fields = ('-created_at',)

    def get_permissions(self):
        if self.action in ['list']:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['create']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'retrieve']:
            permission_classes=[ IsManipalAdminUser ]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes=[IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes=[BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def create(self, request):
        company_serializer = CompanySerializer(data=request.data)
        company_serializer.is_valid(raise_exception=True)
        company_serializer.save()
        return Response(status=status.HTTP_200_OK)

class RequestSyncView(APIView):
    permission_classes = (IsManipalAdminUser,)

    def post(self, request, format=None):
        sync_request = self.request.data.get("sync_request", None)
        if sync_request == 'health_package':
            update_health_package.delay()

        elif sync_request == 'doctor':
            update_doctor.delay()

        elif sync_request == 'item':
            update_item.delay()

        else:
            raise ValidationError("Parameter Missing")

        return Response(status=status.HTTP_200_OK)


class EmergencyContactViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser]
    model = EmergencyContact
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer
    create_success_message = 'Emergency Contact information created successfully!'
    list_success_message = 'Emergency Contact returned successfully!'
    retrieve_success_message = 'Emergency Contact returned successfully!'
    update_success_message = 'Emergency Contact updated successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)


class LinkUhidView(ProxyView):
    permission_classes = [AllowAny]
    source = 'LinkUHID'

    def get_request_data(self, request):
        link_uhid = serializable_LinkUhid(**request.data)
        request_data = custom_serializer().serialize(link_uhid, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        success = False
        message = "Fail"
        if response.status_code == 200:
            message = root.find('msgLinkUHID').text
            if message == "Success":
                success = True
        return self.custom_success_response(success=success, message=message,
                                            data=None)


class ValidateMobileView(ProxyView):
    permission_classes = [AllowAny]
    source = 'ValidatePatient'
    success_msg = 'One time password has been sent on your registered mobile.'

    def get_request_data(self, request):
        mobile = serializable_validate_patient_mobile(**request.data)
        request_data = custom_serializer().serialize(mobile, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        item = root.find('ValidatePatientResp')
        response_content = json.loads(item.text)[0]
        success = str(response_content.get('Status')) == "Pass"
        message = str(response_content.get('Message'))
        return self.custom_success_response(success, message)


class ValidateMobileOTPView(ProxyView):
    permission_classes = [AllowAny]
    source = 'ValidateOTPWeb'
    success_msg = 'OTP validated successfully'

    def get_request_data(self, request):
        uhid_otp = serializable_validate_UHID(**request.data)
        request_data = custom_serializer().serialize(uhid_otp, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        message = None
        item = root.find('ValidateResponse')
        response_content = json.loads(item.text)
        success = False
        
        if  response_content and \
            response_content[0]:
            
            success = True
            message = response_content[0].get('Message')

        if success and not message:
            message = self.success_msg

        return self.custom_success_response(success=success, message=message,
                                            data=response_content)


class UhidConsultationPricingView(ProxyView):
    permission_classes = [AllowAny]
    source = 'getconsultationcharges'

    def get_request_data(self, request):
        consultation_obj = serializable_uhid_based_consultation(**request.data)
        request_data = custom_serializer().serialize(consultation_obj, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        message = "Something went Wrong!!"
        success = False
        item = root.find('consultchargesResp')
        response_content = json.loads(item.text)
        if response_content:

            response_content = response_content[0]
            if "OPDConsCharges" in response_content:
                response_content["OPDConsCharges"] = int(response_content["OPDConsCharges"])
            if "VCConsCharges" in response_content:
                response_content["VCConsCharges"] = int(response_content["VCConsCharges"])
            if "PRConsCharges" in response_content:
                response_content["PRConsCharges"] = int(response_content["PRConsCharges"])
            success = True
            message = "Price returned successfully!!"

        return self.custom_success_response(success=success, message=message,
                                            data=response_content)
class ComponentsView(custom_viewsets.CreateUpdateListRetrieveModelViewSet):

    permission_classes = [AllowAny]
    model = Components
    queryset = Components.objects.all()
    serializer_class = ComponentsSerializer
    create_success_message = 'Component created successfully!'
    list_success_message = 'Component list returned successfully!'
    retrieve_success_message = 'Component returned successfully!'
    update_success_message = 'Component updated successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)

    def get_permissions(self):
        if self.action in ['list']:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['create']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def create(self, request):
        component_serializer = ComponentsSerializer(data=request.data)
        component_serializer.is_valid(raise_exception=True)
        component_serializer.save()
        return Response(status=status.HTTP_200_OK)

class CompanyDomainView(custom_viewsets.CreateUpdateListRetrieveModelViewSet):

    permission_classes = [AllowAny]
    model = CompanyDomain
    queryset = CompanyDomain.objects.all()
    serializer_class = CompanyDomainsSerializer
    create_success_message = 'Company domain created successfully!'
    list_success_message = 'Company domain list retured successfully!'
    retrieve_success_message = 'Company domain returned successfully!'
    update_success_message = 'Company domain updated successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)

    def get_permissions(self):
        if self.action in ['list']:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['create']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def create(self, request):
        component_serializer = ComponentsSerializer(data=request.data)
        component_serializer.is_valid(raise_exception=True)
        component_serializer.save()
        return Response(status=status.HTTP_200_OK)

class ConfigurationsView(custom_viewsets.CreateUpdateListRetrieveModelViewSet):

    permission_classes = [IsPatientUser]
    model = Configurations
    queryset = Configurations.objects.all()
    serializer_class = ConfigurationSerializer
    create_success_message      = 'Method Not Allowed'
    list_success_message        = 'Configurations list retured successfully!'
    retrieve_success_message    = 'Configurations returned successfully!'
    update_success_message      = 'Configurations updated successfully!'
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter,
                filters.OrderingFilter
            )

    def get_permissions(self):
        if self.action in ['list']:
            permission_classes = [IsPatientUser | IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action in ['update','partial_update']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action in ['create']:
            permission_classes = [BlacklistCreateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes=[BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def create(self, request):
        configuration_serializer = ConfigurationSerializer(data=request.data)
        configuration_serializer.is_valid(raise_exception=True)
        configuration_serializer.save()
        return Response(status=status.HTTP_200_OK)

class PatientDetailsByMobileView(ProxyView):
    permission_classes = [IsPatientUser]
    source = 'PatDetailsByMob'
    success_msg = "Patients' list returned successfully"

    def get_request_data(self, request):
        data = request.data
        mobile_number = data.get("mobile")
        data["check_code"] = check_code(mobile_number)
        patient = serializable_patient_details_by_mobile(**request.data)
        request_data = custom_serializer().serialize(patient, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        message = "Error fetching the patients' list"
        item = root.find('PatDetailResp')
        response_content = json.loads(item.text)
        success = False
        
        if  response_content and \
            response_content[0]:
            success = True
            message = self.success_msg
            patient_instance = patient_user_object(self.request)
            for response_data in response_content:

                response_data["isExistingPrimaryUser"] = Patient.objects.filter(uhid_number=response_data.get("HospNo")).exists()
                
                response_data["linkedPatient"] = PatientSerializer(patient_instance,many=False).data if patient_instance.uhid_number and patient_instance.uhid_number==response_data.get("HospNo") else None
                
                linked_family_member = FamilyMember.objects.filter(uhid_number=response_data.get("HospNo"),patient_info__id=patient_instance.id,is_visible=True).first()
                response_data["linkedFamilyMember"] = FamilyMemberSerializer(linked_family_member,many=False).data if linked_family_member else None

        return self.custom_success_response(
                                    success=success, 
                                    message=message,
                                    data=response_content
                                )
        
class MedicineViewSet(custom_viewsets.ReadOnlyModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsPatientUser | IsManipalAdminUser]
    list_success_message = 'Medicines returned successfully!'
    retrieve_success_message = 'Medicine information returned successfully!'
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['name']
    search_fields = ['name']
    
class BillingViewSet(custom_viewsets.ReadOnlyModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [IsPatientUser | IsManipalAdminUser]
    list_success_message = 'Billings returned successfully!'
    retrieve_success_message = 'Billing information returned successfully!'
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['name']
    search_fields = ['name']
    
class HelplineNumbersViewSet(custom_viewsets.CreateUpdateListRetrieveModelViewSet):
    queryset = HelplineNumbers.objects.all()
    serializer_class = HelplineNumbersSerializer
    permission_classes = [IsPatientUser | IsManipalAdminUser]
    create_success_message = 'Helpline number added successfully!'
    update_success_message = 'Helpline number updated successfully!'
    list_success_message = 'Helpline numbers returned successfully!'
    retrieve_success_message = 'Helpline number returned successfully!'
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['hospital_ids','hospital_ids__code','company_id','company_id__name','component_id__code']
    search_fields = ['contact_number','hospital_ids__code','hospital_ids__description','company_id__name','component_id__code']
    ordering_fields = ('hospital_ids','company_id','component_id','-created_at',)
    
    def get_permissions(self):

        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPatientUser | IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action in ['create','partial_update']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]
        
        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

@api_view(['POST'])
@permission_classes([AllowAny])
def send_invite(request):
    appointment_id = request.data.get('appointment_id')
    appointment_obj = Appointment.objects.filter(appointment_identifier=appointment_id).first()
    if appointment_obj and send_appointment_invitation(appointment_obj):
        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FeedbackRecipientsViewSet(custom_viewsets.ModelViewSet):
    queryset = FeedbackRecipients.objects.all()
    serializer_class = FeedbackRecipientSerializer
    permission_classes = [IsManipalAdminUser]
    create_success_message = 'Feedback recipient information added successfully!'
    update_success_message = 'Feedback recipient information updated successfully!'
    list_success_message = 'Feedback recipients information returned successfully!'
    retrieve_success_message = 'Feedback recipient information returned successfully!'
    delete_success_message = 'Feedback recipient information deleted successfully!'
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['hospital_code','type']
    search_fields = ['hospital_code','name','contact','email'] 
    