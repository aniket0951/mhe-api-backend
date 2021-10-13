from apps.home_care.serializers import HealthTestCartItemsSerializer, LabTestAppointmentSerializer, LabTestSlotScheduleSerializer, LabTestSlotsWeeklyMasterSerializer
from utils.custom_permissions import BlacklistDestroyMethodPermission, BlacklistUpdateMethodPermission, IsManipalAdminUser, IsPatientUser
from .serializers import HomeCareHealthTestSerializer, HealthTestPricingSerializer
from utils import custom_viewsets
from .models import HealthTest, HealthTestCartItems, HealthTestPricing, LabTestAppointment, LabTestSlotSchedule, LabTestSlotsWeeklyMaster
from rest_framework import filters, status
from django_filters.rest_framework import DjangoFilterBackend


class HealthTestViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    queryset = HealthTest.objects.all()
    serializer_class = HomeCareHealthTestSerializer

    create_success_message = 'Health test added successfully!'
    list_success_message = 'Health test informations returned successfully!'
    retrieve_success_message = 'Health test information retrived successfully!'
    update_success_message = 'Health test information updated successfully!'

    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    
    filter_fields = ['code','description','health_test_category__code','health_test_category__name']
    search_fields = ['description','code']
    
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

    
class HealthTestPricingViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    queryset = HealthTestPricing.objects.all()
    serializer_class = HealthTestPricingSerializer

    create_success_message = 'Health test pricing added successfully!'
    list_success_message = 'Health test pricing informations returned successfully!'
    retrieve_success_message = 'Health test pricing information retrived successfully!'
    update_success_message = 'Health test pricing information updated successfully!'

    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    
    filter_fields = ['hospital__code','hospital__id','health_test__code']
    search_fields = ['hospital__code','hospital__description','hospital__id','health_test__code']

    
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

    
class HealthTestCartItemViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    queryset = HealthTestCartItems.objects.all()
    serializer_class = HealthTestCartItemsSerializer

    create_success_message = 'Health test cart items added successfully!'
    list_success_message = 'Health test cart items returned successfully!'
    retrieve_success_message = 'Health test cart items  retrived successfully!'
    update_success_message = 'Health test cart items  updated successfully!'

    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['health_test__code','health_test__description','hospital__code','hospital__description','hospital__id']
    search_fields = ['hospital__code','hospital__description','hospital__id','health_test__code','health_test__description']

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

    
class LabTestAppointmentViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    queryset = LabTestAppointment.objects.all()
    serializer_class = LabTestAppointmentSerializer

    create_success_message = 'Lab test appointment created successfully!'
    list_success_message = 'Lab test appointments returned successfully!'
    retrieve_success_message = 'Lab test appointment retrived successfully!'
    update_success_message = 'Lab test appointment updated successfully!'
    delete_success_message = 'Lab test appointment deleted successfully!'

    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )

    filter_fields = ['health_test__code','hospital__code','patient__uhid','patient__first_name','family_member__uhid','family_memer__first_name','phlebo__first_name']
    search_fields = ['hospital__code','hospital__description','hospital__id','health_test__code','health_test__description','patient__uhid','patient__first_name','family_member__uhid','family_memer__first_name','phlebo__first_name']

    def get_permissions(self):

        if self.action in ['create','partial_update']:
            permission_classes = [IsPatientUser]
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

    
class LabTestSlotsWeeklyMasterViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    queryset = LabTestSlotsWeeklyMaster.objects.all()
    serializer_class = LabTestSlotsWeeklyMasterSerializer

    create_success_message = 'Lab test weekly slot added successfully!'
    list_success_message = 'Lab test weekly slots returned successfully!'
    retrieve_success_message = 'Lab test weekly slot retrived successfully!'
    update_success_message = 'Lab test weekly slot updated successfully!'

    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['hospital__code','hospital__id','day']
    search_fields = ['hospital__code','hospital__description','hospital__id']

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

    
class LabTestSlotScheduleViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    queryset = LabTestSlotSchedule.objects.all()
    serializer_class = LabTestSlotScheduleSerializer

    create_success_message = 'Lab test slot scheduled successfully!'
    list_success_message = 'Lab test slot scheduled returned successfully!'
    retrieve_success_message = 'Lab test slot scheduled retrived successfully!'
    update_success_message = 'Lab test slot scheduled updated successfully!'

    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    
    filter_fields = ['hospital__code','hospital__id','phlebo__first_name']
    search_fields = ['hospital__code','hospital__description','hospital__id','phlebo__first_name','pin']

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
