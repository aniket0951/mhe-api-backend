
import re
from .utils import AdditionalFeaturesUtil
from datetime import datetime, timedelta
import ast

from proxy.custom_views import ProxyView
import logging
from utils.utils import get_uhid_number_queryset, manipal_admin_object, patient_user_object
from .serializers import DriveBookingSerializer, DriveInventorySerializer, DriveSerializer, StaticInstructionsSerializer
from .models import Drive,  DriveBooking, DriveInventory, StaticInstructions
from utils import custom_viewsets
from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.crypto import get_random_string

from utils.custom_permissions import (BlacklistDestroyMethodPermission, BlacklistUpdateMethodPermission,
                                      BlacklistCreateMethodPermission, IsPatientUser, IsManipalAdminUser,
                                      IsPccUserPermission)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.serializers import ValidationError
from ratelimit.decorators import ratelimit
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.db.models import Q

import xml.etree.ElementTree as ET
from proxy.custom_serializables import DriveItemPrice as serializable_DriveItemPrice
from proxy.custom_serializers import ObjectSerializer as custom_serializer

from apps.patients.emails import send_corporate_email_activation_otp
from apps.patients.exceptions import InvalidEmailOTPException, OTPExpiredException
from apps.patients.constants import PatientsConstants
from apps.patients.models import FamilyMember
from apps.patients.serializers import PatientSerializer

OTP_LENGTH = settings.OTP_LENGTH
logger = logging.getLogger("django")


class StaticInstructionsViewSet(custom_viewsets.ReadOnlyModelViewSet):
    queryset = StaticInstructions.objects.all()
    serializer_class = StaticInstructionsSerializer
    permission_classes = [IsPatientUser]
    list_success_message = 'Static Instructions returned successfully!'
    retrieve_success_message = 'Static Instruction returned successfully!'
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    )
    filter_fields = ['instruction_type']


class DriveScheduleViewSet(custom_viewsets.CreateUpdateListRetrieveModelViewSet):
    queryset = Drive.objects.all()
    serializer_class = DriveSerializer
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    create_success_message = 'Drive Schedule created successfully!'
    list_success_message = 'Drive Schedules returned successfully!'
    retrieve_success_message = 'Drive Schedule information returned successfully!'
    update_success_message = 'Drive Schedules updated successfully!'

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    )
    filter_fields = ['type', 'date', 'hospital__code', 'code']
    search_fields = ['description', 'code']
    ordering = ('-date', '-created_at')
    ordering_fields = ('-date', '-created_at')

    def get_permissions(self):

        if self.action in ['create', 'partial_update']:
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

        code = self.request.query_params.get('code')
        if patient_user_object(self.request):
            AdditionalFeaturesUtil.validate_drive_code(code)

        admin_object = manipal_admin_object(self.request)
        if admin_object and admin_object.hospital:
            qs = qs.filter(hospital__id=admin_object.hospital.id)

        return qs

    def perform_create(self, serializer):
        request_data = self.request.data

        AdditionalFeaturesUtil.datetime_validation_on_creation(request_data)

        serializer.validated_data['code'] = AdditionalFeaturesUtil.generate_unique_drive_code(
            serializer.validated_data['description'])

        serializer_id = serializer.save(is_active=True)

        AdditionalFeaturesUtil.generate_qr_code(
            serializer.validated_data['code'], serializer_id)

        AdditionalFeaturesUtil.create_drive_inventory(
            serializer_id.id, request_data)
        AdditionalFeaturesUtil.create_drive_billing(
            serializer_id.id, request_data)

    def perform_update(self, serializer):
        request_data = self.request.data

        AdditionalFeaturesUtil.datetime_validation_on_updation(request_data)

        serializer_id = serializer.save()

        AdditionalFeaturesUtil.update_drive_inventory(
            serializer_id.id, request_data)
        AdditionalFeaturesUtil.update_drive_billing(
            serializer_id.id, request_data)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def generate_drive_corporate_email_verification_otp(self, request):

        authenticated_patient = patient_user_object(request)
        drive = self.request.data.get("drive")
        drive_corporate_email = self.request.data.get("drive_corporate_email")

        drive_email_domain = re.search('@.*', drive_corporate_email).group()

        drive_id = Drive.objects.filter(id=drive).first()

        if drive_email_domain != drive_id.domain:
            raise ValidationError("Invalid Corporate Email")

        random_email_otp = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        send_corporate_email_activation_otp(
            str(authenticated_patient.id), drive_corporate_email, random_email_otp)

        authenticated_patient.drive_corporate_email = drive_corporate_email
        authenticated_patient.drive_corporate_email_otp = random_email_otp
        authenticated_patient.drive_corporate_email_otp_expiration_time = otp_expiration_time
        authenticated_patient.save()

        data = {
            "data": {"email": str(authenticated_patient.drive_corporate_email), },
            "message": PatientsConstants.OTP_EMAIL_SENT,
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def verify_drive_corporate_email_otp(self, request):
        drive_email_otp = request.data.get('drive_email_otp')
        authenticated_patient = patient_user_object(request)

        if not authenticated_patient.drive_corporate_email_otp == drive_email_otp:
            raise InvalidEmailOTPException

        if datetime.now().timestamp() > authenticated_patient.drive_corporate_email_otp_expiration_time.timestamp():
            raise OTPExpiredException

        random_email_otp = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')

        authenticated_patient.drive_corporate_email_otp = random_email_otp
        authenticated_patient.save()

        data = {
            "data": PatientSerializer(authenticated_patient).data,
            "message": "Your email is verified successfully!"
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def validate_user(self, request):

        AdditionalFeaturesUtil.validate_patient_age(request.data.get('dob'))

        patient_user = patient_user_object(self.request)
        if not patient_user or not request.data.get('drive'):
            raise ValidationError("Provide a valid drive ID!")

        AdditionalFeaturesUtil.validate_if_the_drive_is_already_booked(
            request, request.data.get('drive'), patient_user)

        data = {
            "data": DriveSerializer(Drive.objects.get(id=request.data.get('drive')), context={'request': request}).data,
            "message": "User details are verified successfully!"
        }
        return Response(data, status=status.HTTP_200_OK)


class DriveItemCodePriceView(ProxyView):
    permission_classes = [AllowAny, ]
    source = 'OPItemPrice'

    def get_request_data(self, request):
        item_code_price = serializable_DriveItemPrice(**request.data)
        request_data = custom_serializer().serialize(item_code_price, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        response_message = {}
        message = "Could not fetch the price for the Item Code"
        success = False
        item_price_details = root.find("OPItemPriceDetails").text
        if status == "1" and item_price_details:
            item_price_details_json = ast.literal_eval(item_price_details)
            response_message = item_price_details_json
            message = "success"
            success = True
        return self.custom_success_response(
            message=message,
            success=success,
            data=response_message
        )

    def perform_update(self, serializer):
        serializer.save()


class DriveInventoryViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser]
    model = DriveInventory
    queryset = DriveInventory.objects.all()
    serializer_class = DriveInventorySerializer
    create_success_message = 'Drive Inventory added successfully!'
    list_success_message = 'Drive Inventories returned successfully!'
    retrieve_success_message = 'Drive Inventory returned successfully!'
    update_success_message = 'Drive Inventory updated successfully!'
    delete_success_message = 'Drive Inventory deleted successfully!'


class DriveBookingViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    model = DriveBooking
    queryset = DriveBooking.objects.all()
    serializer_class = DriveBookingSerializer
    create_success_message = 'Drive booked successfully!'
    list_success_message = 'Drive Bookings returned successfully!'
    retrieve_success_message = 'Drive Booking returned successfully!'
    update_success_message = 'Drive Booking updated successfully!'
    delete_success_message = 'Drive Booking deleted successfully!'

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    )
    filter_fields = ['status', 'drive__hospital__code',
                     'drive_inventory__medicine__name', 'drive__date', 'drive__id', 'drive__code']
    search_fields = ['patient__first_name', 'family_member__first_name', 'patient__uhid_number',
                     'family_member__uhid_number', 'drive__description', 'drive__code', 'beneficiary_reference_id', 'booking_number']
    ordering = ('-drive__date', '-created_at')
    ordering_fields = ('-drive__date', '-created_at')

    def get_permissions(self):

        if self.action in ['partial_update']:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPatientUser | IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action == 'create':
            permission_classes = [BlacklistCreateMethodPermission]
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
        is_upcoming = self.request.query_params.get("is_upcoming", False)
        family_member_id = self.request.query_params.get("user_id", None)
        patient_instace = patient_user_object(self.request)
        family_member = FamilyMember.objects.filter(
            id=family_member_id).first()

        if patient_instace:

            qs = qs.filter(Q(status__in=[DriveBooking.BOOKING_BOOKED]))

            uhid_number = patient_instace.uhid_number
            if family_member:
                uhid_number = family_member.uhid_number

            uhid_number_queryset = get_uhid_number_queryset(uhid_number)

            if family_member:
                qs = qs.filter(
                    uhid_number_queryset
                    | (
                        Q(family_member__isnull=False) &
                        Q(family_member_id=family_member.id)
                    )
                )
            else:
                qs = qs.filter(
                    uhid_number_queryset
                    | (
                        Q(family_member__isnull=True) &
                        Q(patient_id=patient_instace.id)
                    )
                )

            if is_upcoming:
                qs = qs.filter(Q(drive__date__gte=datetime.now().date()))
            else:
                qs = qs.filter(Q(drive__date__lt=datetime.now().date()))

        admin_object = manipal_admin_object(self.request)
        if admin_object:
            date_from = self.request.query_params.get("date_from", None)
            date_to = self.request.query_params.get("date_to", None)
            patient_id = self.request.query_params.get("patient_id", None)
            family_member_id = self.request.query_params.get(
                "family_member_id", None)

            if admin_object.hospital:
                qs = qs.filter(drive__hospital__id=admin_object.hospital.id)
            if date_from and date_to:
                qs = qs.filter(drive__date__range=[date_from, date_to])
            if patient_id:
                qs = qs.filter(patient__id=patient_id, family_member__isnull=True).order_by(
                    '-created_at').distinct()
            if family_member_id:
                qs = qs.filter(family_member__id=family_member_id).order_by(
                    '-created_at').distinct()
            return qs

        return qs

    @action(detail=False, methods=['POST'])
    def book_drive(self, request):

        patient = patient_user_object(self.request)
        if not patient:
            raise ValidationError("Not authorized")

        drive_id, drive_inventory, amount, dob, aadhar_number = None, None, None, None, None
        for filter_field in ["status", "booking_number", "payment"]:
            if filter_field in request.data:
                request.data.pop(filter_field)

        try:

            drive_id = request.data['drive']
            drive_inventory = request.data['drive_inventory']
            amount = request.data['amount']
            dob = request.data.pop('dob')
            aadhar_number = request.data.pop('aadhar_number')
            request.data['beneficiary_reference_id']
            request.data['booking_number'] = AdditionalFeaturesUtil.generate_unique_booking_number()

        except Exception as e:
            logger.error(
                "DriveBookingViewSet -> book_drive : Error while booking an appointment : %s" % (str(e)))
            raise ValidationError("Required field : %s" % str(e))

        AdditionalFeaturesUtil.validate_patient_age(dob)
        AdditionalFeaturesUtil.validate_if_the_drive_is_already_booked(
            request, drive_id, patient)
        AdditionalFeaturesUtil.validate_inventory(drive_inventory, drive_id)
        AdditionalFeaturesUtil.update_user_data(
            request, dob, aadhar_number, patient)

        request.data['patient'] = patient.id
        drive_booking_serializer = DriveBookingSerializer(data=request.data)
        drive_booking_serializer.is_valid(raise_exception=True)
        drive_booking = drive_booking_serializer.save()

        payment_params = AdditionalFeaturesUtil.validate_and_prepare_payment_data(
            request, patient, drive_booking, amount)

        return Response(data={
            "drive_booking": DriveBookingSerializer(DriveBooking.objects.get(id=drive_booking.id)).data,
            "params": payment_params
        }, status=status.HTTP_200_OK)
