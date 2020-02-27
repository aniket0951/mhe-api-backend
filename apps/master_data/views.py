import json
import xml.etree.ElementTree as ET
from datetime import datetime

from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.doctors.models import Doctor
from apps.health_packages.models import HealthPackage, HealthPackagePricing
from apps.health_tests.models import HealthTest
from apps.lab_and_radiology_items.models import (LabRadiologyItem,
                                                 LabRadiologyItemPricing)
from proxy.custom_endpoints import SYNC_SERVICE, VALIDATE_OTP, VALIDATE_UHID
from proxy.custom_serializables import \
    ItemTaiffPrice as serializable_ItemTariffPrice
from proxy.custom_serializables import \
    ValidateUHID as serializable_validate_UHID
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from utils import custom_viewsets

from .models import (BillingGroup, BillingSubGroup, Department, Hospital,
                     HospitalDepartment, Specialisation)
from .serializers import HospitalSerializer


class HospitalViewSet(custom_viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    model = Hospital
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    create_success_message = None
    list_success_message = 'Hospitals list returned successfully!'
    retrieve_success_message = 'Hospital information returned successfully!'
    update_success_message = None

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]
        return super().get_permissions()


class DepartmentsView(ProxyView):
    # permission_classes = [IsAuthenticated]
    source = SYNC_SERVICE
    success_msg = 'Departments list returned successfully'
    sync_method = 'department'

    def get_request_data(self, request):
        return self.get_sync_request_data(request)

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        item = root.find('SyncResponse')

        if item.text.startswith('Request Parameter'):
            return self.custom_success_response(message='Missing hospital location code.',
                                                success=False, data=None, error=str(item.text))
        try:
            response_content = json.loads(item.text)
        except Exception:
            return self.custom_success_response(message='Looks like you have entered an invalid location code.',
                                                success=False, data=None, error=str(item.text))

        all_departments = list()
        department_sorted_keys = ['start_date',
                                  'end_date',
                                  'code',
                                  'name',
                                  'hospital_code'
                                  ]
        for each_department in response_content:
            department_details = dict()
            for index, key in enumerate(sorted(each_department.keys())):
                if not each_department[key]:
                    each_department[key] = None

                if key in ['DateFrom', 'DateTo'] and each_department[key]:
                    each_department[key] = datetime.strptime(
                        each_department[key], '%d/%m/%Y').strftime('%Y-%m-%d')

                department_details[department_sorted_keys[index]
                                   ] = each_department[key]
            department_kwargs = dict()
            hospital_department_details = dict()
            hospital_department_kwargs = dict()
            hospital_code = department_details.pop('hospital_code')
            hospital_department_details['start_date'] = department_details.pop(
                'start_date')
            hospital_department_details['end_date'] = department_details.pop(
                'end_date')
            hospital = Hospital.objects.filter(code=hospital_code).first()

            department_kwargs['code'] = department_details['code']
            department, department_created = Department.objects.update_or_create(
                **department_kwargs, defaults=department_details)
            department_details['department_created'] = department_created

            hospital_department_kwargs['hospital'] = hospital
            hospital_department_kwargs['department'] = department
            hospital_department_details.update(hospital_department_kwargs)

            hospital_department, hospital_department_created = HospitalDepartment.objects.update_or_create(
                **hospital_department_kwargs, defaults=hospital_department_details)
            department_details['hospital_department_created'] = hospital_department_created

            all_departments.append(department_details)

        return self.custom_success_response(message=self.success_msg,
                                            success=True, data=all_departments)


class DoctorsView(ProxyView):
    # permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    source = SYNC_SERVICE
    success_msg = 'Doctors list returned successfully'
    sync_method = 'doctor'

    def get_request_data(self, request):
        return self.get_sync_request_data(request)

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        item = root.find('SyncResponse')
        if item.text.startswith('Request Parameter'):
            return self.custom_success_response(message='Missing doctors location code.',
                                                success=False, data=None, error=str(item.text))

        try:
            response_content = json.loads(item.text)
        except Exception as e:
            print("------------------------\nFailed!\n----------------")
            return self.custom_success_response(message="Couldn't process the doctors at this location.",
                                                success=False, data=None, error=str(item.text))

        if not response_content:
            return self.custom_success_response(message='Invalid doctors location code.',
                                                success=False, data=None)

        all_doctors = list()
        doctor_sorted_keys = ['consultation_charges',
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
                              'specialisation_code',
                              'specialisation_description',
                              ]
        for each_doctor in response_content:
            doctor_details = dict()
            for index, key in enumerate(sorted(each_doctor.keys())):
                if key in ['DocProfile', 'DeptName', 'SpecDesc']:
                    continue

                if not each_doctor[key]:
                    each_doctor[key] = None

                if key in ['DateFrom', 'DateTo'] and each_doctor[key]:
                    each_doctor[key] = datetime.strptime(
                        each_doctor[key], '%d/%m/%Y').strftime('%Y-%m-%d')

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

            doctor, doctor_created = Doctor.objects.update_or_create(
                **doctor_kwargs, defaults=doctor_details)
            doctor_details['doctor_created'] = doctor_created
            if hospital_department_obj:
                doctor.hospital_departments.add(hospital_department_obj)
            if specialisation_obj:
                doctor.specialisations.add(specialisation_obj)
            all_doctors.append(doctor_details)

        return self.custom_success_response(message=self.success_msg,
                                            success=True, data=all_doctors)


class HealthPackagesView(ProxyView):
    permission_classes = [AllowAny]
    source = SYNC_SERVICE
    success_msg = 'Health Packages list returned successfully'
    sync_method = 'healthcheck'

    def get_request_data(self, request):
        return self.get_sync_request_data(request)

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        item = root.find('SyncResponse')
        if item.text.startswith('Request Parameter'):
            return self.custom_success_response(message='Missing location code.',
                                                success=False, data=None, error=str(item.text))
        try:
            response_content = json.loads(item.text, strict=False)
        except Exception as e:
            return self.custom_success_response(message='Looks like you have entered an invalid location code.',
                                                success=False, data=None, error=str(item.text))

        all_health_packages = list()
        health_packages_sorted_keys = ['billing_group',
                                       'billing_subgroup',
                                       'start_date',
                                       'end_date',
                                       'hospital_code',
                                       'item_code',
                                       'item_description',
                                       'code',
                                       'name',
                                       'price',
                                       ]
        for each_health_package in response_content:
            health_package_details = dict()
            for index, key in enumerate(sorted(each_health_package.keys())):
                if not each_health_package[key]:
                    each_health_package[key] = None

                if key in ['DateFrom', 'DateTo'] and each_health_package[key]:
                    each_health_package[key] = datetime.strptime(
                        each_health_package[key], '%d/%m/%Y').strftime('%Y-%m-%d')

                health_package_details[health_packages_sorted_keys[index]
                                       ] = each_health_package[key]

            health_package_kwargs = dict()
            hospital_health_package_details = dict()
            hospital_health_package_kwargs = dict()
            health_test_details = dict()
            health_test_kwargs = dict()
            health_test_billing_group = None
            health_test_billing_subgroup = None
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

            hospital = Hospital.objects.filter(code=hospital_code).first()

            health_package_kwargs['code'] = health_package_details['code']
            health_package, health_package_created = HealthPackage.objects.update_or_create(
                **health_package_kwargs, defaults=health_package_details)
            health_package.included_health_tests.add(health_test)

            hospital_health_package_kwargs['hospital'] = hospital
            hospital_health_package_kwargs['health_package'] = health_package
            hospital_health_package_details.update(
                hospital_health_package_kwargs)

            hospital_health_package, hospital_health_package_created = HealthPackagePricing.objects.update_or_create(
                **hospital_health_package_kwargs, defaults=hospital_health_package_details)

            health_package_details['health_test_created'] = health_test_created
            health_package_details['health_package_created'] = health_package_created
            health_package_details['hospital_health_package_created'] = hospital_health_package_created

            all_health_packages.append(health_package_details)

        return self.custom_success_response(message=self.success_msg,
                                            success=True, data=response_content)


class LabRadiologyItemsView(ProxyView):
    permission_classes = [AllowAny]
    source = SYNC_SERVICE
    success_msg = 'Lab Radiology items list returned successfully'
    sync_method = 'labraditems'

    def get_request_data(self, request):
        return self.get_sync_request_data(request)

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        item = root.find('SyncResponse')
        if item.text.startswith('Request Parameter'):
            return self.custom_success_response(message='Missing location code.',
                                                success=False, data=None, error=str(item.text))
        try:
            response_content = json.loads(item.text)
        except Exception:
            return self.custom_success_response(message='Looks like you have entered an invalid location code.',
                                                success=False, data=None, error=str(item.text))

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
            hospital_lab_radiology_item_details = dict()
            for index, key in enumerate(sorted(each_lab_radiology_item.keys())):
                if not each_lab_radiology_item[key]:
                    each_lab_radiology_item[key] = None

                if key in ['DateFrom', 'DateTo'] and each_lab_radiology_item[key]:
                    each_lab_radiology_item[key] = datetime.strptime(
                        each_lab_radiology_item[key], '%d/%m/%Y').strftime('%Y-%m-%d')

                hospital_lab_radiology_item_details[lab_radiology_items_sorted_keys[index]
                                       ] = each_lab_radiology_item[key]

            lab_radiology_item_kwargs = dict()
            lab_radiology_item_details = dict()
            hospital_lab_radiology_item_kwargs = dict()
            lab_radiology_item_billing_group = None
            lab_radiology_item_billing_subgroup = None

            lab_radiology_item_details['billing_group'] = hospital_lab_radiology_item_details.pop(
                'billing_group')
            lab_radiology_item_details['billing_sub_group'] = hospital_lab_radiology_item_details.pop(
                'billing_subgroup')
            lab_radiology_item_details['description'] = hospital_lab_radiology_item_details.pop(
                'description')
            lab_radiology_item_kwargs['code'] = hospital_lab_radiology_item_details.pop(
                'code')

            if lab_radiology_item_details['billing_group']:
                lab_radiology_item_details['billing_group'] = BillingGroup.objects.filter(
                    description=lab_radiology_item_details['billing_group']).first()

            if lab_radiology_item_details['billing_sub_group']:
                lab_radiology_item_details['billing_sub_group'] = BillingSubGroup.objects.filter(
                    description=lab_radiology_item_details['billing_sub_group']).first()

            lab_radiology_item, lab_radiology_item_created = LabRadiologyItem.objects.update_or_create(
                **lab_radiology_item_kwargs, defaults=lab_radiology_item_details)

            hospital_code = hospital_lab_radiology_item_details.pop('hospital_code')
            hospital = Hospital.objects.filter(code=hospital_code).first()

            hospital_lab_radiology_item_kwargs['item'] = lab_radiology_item
            hospital_lab_radiology_item_kwargs['hospital'] = hospital

            hospital_lab_radiology_item, hospital_lab_radiology_item_created = LabRadiologyItemPricing.objects.update_or_create(
                **hospital_lab_radiology_item_kwargs, defaults=hospital_lab_radiology_item_details)

            hospital_lab_radiology_item_details['hospital_lab_radiology_item_created'] = hospital_lab_radiology_item_created
            hospital_lab_radiology_item_details['lab_radiology_item_created'] = lab_radiology_item_created

            all_lab_radiology_items.append(hospital_lab_radiology_item_details)

        return self.custom_success_response(message=self.success_msg,
                                            success=True, data=all_lab_radiology_items)


class ItemsTarrifPriceView(ProxyView):
    # permission_classes = [IsAuthenticated]
    source = SYNC_SERVICE
    success_msg = 'Lab Radiology items list returned successfully'
    sync_method = 'tariff'

    def get_request_data(self, request):
        request.data['sync_method'] = self.sync_method
        health_packages = serializable_ItemTariffPrice(**request.data)
        request_data = custom_serializer().serialize(health_packages, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response._content)
        item = root.find('SyncResponse')

        try:
            response_content = json.loads(item.text)
        except Exception:
            return self.custom_success_response(message='Something went wrong, enter valid location code and item code.',
                                                success=False, data=None, error=str(item.text))

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
