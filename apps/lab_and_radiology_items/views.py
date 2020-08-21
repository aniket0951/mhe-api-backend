from django.db.models import Exists, OuterRef, Q
from django.utils.timezone import datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ValidationError

from apps.cart_items.models import HomeCollectionCart
from apps.master_data.models import BillingGroup, HomeCareService
from apps.patients.exceptions import InvalidFamilyMemberValidationException
from apps.patients.models import FamilyMember, Patient
from utils import custom_viewsets
from utils.custom_permissions import (BlacklistDestroyMethodPermission,
                                      BlacklistUpdateMethodPermission,
                                      IsManipalAdminUser, IsPatientUser)
from utils.utils import manipal_admin_object, patient_user_object

from .models import (HomeCollectionAppointment, LabRadiologyItem,
                     LabRadiologyItemPricing, PatientServiceAppointment)
from .serializers import (HomeCareServiceSerializer,
                          HomeCollectionAppointmentSerializer,
                          LabRadiologyItemSerializer,
                          PatientServiceAppointmentSerializer)


class HomeCollectionViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = LabRadiologyItem
    queryset = LabRadiologyItem.objects.all().order_by('description')
    serializer_class = LabRadiologyItemSerializer
    create_success_message = "New home collection is added successfully."
    list_success_message = 'Home collection list returned successfully!'
    retrieve_success_message = 'Home collection information returned successfully!'
    update_success_message = 'Home collection information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter,)
    search_fields = ['description', ]

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
        hospital_id = self.request.query_params.get('hospital__id')
        if not hospital_id:
            raise ValidationError("Hospital ID is missiing!")

        home_collection_billing_group = BillingGroup.objects.filter(
            description='Lab Diagnostic Services').first()

        hospital_related_items = LabRadiologyItemPricing.objects.filter(
            hospital=hospital_id).filter((Q(end_date__gte=datetime.now().date()) | Q(end_date__isnull=True)) &
            Q(start_date__lte=datetime.now().date())).values_list('item_id', flat=True)

        user_cart_collections = HomeCollectionCart.objects.filter(
            patient_info_id=self.request.user.id,  home_collections=OuterRef('pk'), hospital_id=hospital_id)

        return super().get_queryset().filter(id__in=hospital_related_items,
                                               billing_group=home_collection_billing_group)\
            .distinct().annotate(is_added_to_cart=Exists(user_cart_collections))


class HomeCareServiceViewSet(custom_viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    model = HomeCareService
    queryset = HomeCareService.objects.all()
    serializer_class = HomeCareServiceSerializer
    list_success_message = 'Home care services list returned successfully!'
    retrieve_success_message = 'Home care service information returned successfully!'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]
        return super().get_permissions()


class PatientServiceAppointmentViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = PatientServiceAppointment
    queryset = PatientServiceAppointment.objects.all()
    serializer_class = PatientServiceAppointmentSerializer
    create_success_message = "New service appointment is added successfully."
    list_success_message = 'Service appointment list returned successfully!'
    retrieve_success_message = 'Service appointment information returned successfully!'
    update_success_message = 'Service appointment information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    ordering_fields = ('appointment_date',)
    filter_fields = ('status',)
    search_fields = ('patient__first_name', 'patient__uhid_number',
                     'patient__mobile',
                     'family_member__first_name', 'family_member__uhid_number',
                     'family_member__mobile',
                     'service__name')

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPatientUser | IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action in ['create', ]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'partial_update':
            permission_classes = [IsManipalAdminUser | IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        qs=super().get_queryset()
        
        if manipal_admin_object(self.request):
            date_from = self.request.query_params.get("date_from", None)
            date_to = self.request.query_params.get("date_to", None)
            if date_from and date_to:
                qs = qs.filter(appointment_date__range=[date_from, date_to])
            return qs  
        

        family_member = self.request.query_params.get("user_id", None)
        if family_member is not None:
            member = FamilyMember.objects.filter(id=family_member,
                                                 patient_info_id=self.request.user.id).first()
            if not member:
                raise InvalidFamilyMemberValidationException
            return super().get_queryset().filter(Q(family_member_id=family_member) | (Q(patient_id__uhid_number__isnull=False) & Q(patient_id__uhid_number=member.uhid_number) & Q(family_member__isnull=True))
                                                 | (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=member.uhid_number)))
        else:
            patient = Patient.objects.filter(id=self.request.user.id).first()
            return super().get_queryset().filter((Q(patient_id=patient.id) & Q(family_member__isnull=True)) |
                                                 (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=patient.uhid_number)))


class HomeCollectionAppointmentViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = HomeCollectionAppointment
    queryset = HomeCollectionAppointment.objects.all()
    serializer_class = HomeCollectionAppointmentSerializer
    create_success_message = "New home collection appointment is added successfully."
    list_success_message = 'Home collection appointment list returned successfully!'
    retrieve_success_message = 'Home collection appointment information returned successfully!'
    update_success_message = 'Home collection appointment information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    ordering_fields = ('appointment_date',)
    filter_fields = ('status',)
    search_fields = ('patient__first_name', 'patient__uhid_number',
                     'patient__mobile',
                     'family_member__first_name', 'family_member__uhid_number',
                     'family_member__mobile',)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPatientUser | IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action in ['create', ]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'partial_update':
            permission_classes = [IsManipalAdminUser | IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        qs=super().get_queryset()
        if manipal_admin_object(self.request):
            date_from = self.request.query_params.get("date_from", None)
            date_to = self.request.query_params.get("date_to", None)
            if date_from and date_to:
                qs = qs.filter(appointment_date__range=[date_from, date_to])
            return qs    
        family_member = self.request.query_params.get("user_id", None)
        if family_member is not None:
            member = FamilyMember.objects.filter(id=family_member,
                                                 patient_info_id=self.request.user.id).first()
            if not member:
                raise InvalidFamilyMemberValidationException
            return super().get_queryset().filter(Q(family_member_id=family_member) | (Q(patient_id__uhid_number__isnull=False) & Q(patient_id__uhid_number=member.uhid_number) & Q(family_member__isnull=True))
                                                 | (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=member.uhid_number)))
        else:
            patient = Patient.objects.filter(id=self.request.user.id).first()
            return super().get_queryset().filter((Q(patient_id=patient.id) & Q(family_member__isnull=True)) |
                                                 (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=patient.uhid_number)))

    def perform_create(self, serializer):
        serializer.save()
        patient_user = patient_user_object(self.request)
        cart_obj = HomeCollectionCart.objects.filter(
            patient_info=patient_user).first()
        if cart_obj:
            cart_obj.home_collections.clear()
