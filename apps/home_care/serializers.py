import logging
from apps.appointments.serializers import CancellationReasonSerializer
from apps.doctors.serializers import HospitalSerializer
from apps.payments.serializers import PaymentSerializer
from apps.phlebo.serializers import PhleboSerializer
from utils.utils import generate_pre_signed_url
from .models import HealthTestCartItems, HealthTestCategory,HealthTest, HealthTestPricing, HospitalRegion, LabTestAppointment, LabTestAppointmentHistory, LabTestSlotSchedule, LabTestSlotsMaster, LabTestSlotsWeeklyMaster
from apps.patients.serializers import FamilyMemberSerializer, PatientAddressSerializer, PatientSerializer
from utils.serializers import DynamicFieldsModelSerializer

logger = logging.getLogger('django')

class HealthTestCategorySerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = HealthTestCategory
        fields = '__all__'
    
class HomeCareHealthTestSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = HealthTest
        fields = '__all__'
    
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.health_test_category:
            response_object['health_test_category'] = HealthTestCategorySerializer(instance.health_test_category).data
        return response_object

class HealthTestPricingSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = HealthTestPricing
        fields = '__all__'
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.health_test:
            response_object['health_test'] = HomeCareHealthTestSerializer(instance.health_test).data
        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(instance.hospital).data
        return response_object
        
class HealthTestCartItemsSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = HealthTestCartItems
        fields = '__all__'
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.health_test:
            response_object['health_test'] = HomeCareHealthTestSerializer(instance.health_test, many=True).data
        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(instance.hospital).data
        if instance.patient:
            response_object['patient'] = PatientSerializer(instance.patient).data
        return response_object
    
class LabTestAppointmentSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = LabTestAppointment
        fields = '__all__'
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        try:
            if instance.hospital:
                response_object['hospital'] = HospitalSerializer(instance.hospital).data
            if instance.health_tests:
                response_object['health_tests'] = HomeCareHealthTestSerializer(instance.health_tests, many=True).data 
            if instance.patient:
                response_object['patient'] = PatientSerializer(instance.patient).data
            if instance.family_member:
                response_object['family_member'] = FamilyMemberSerializer(instance.family_member).data
            if instance.payment:
                response_object['payment'] = PaymentSerializer(instance.payment).data
            if instance.reason:
                response_object['reason'] = CancellationReasonSerializer(instance.reason).data
            if instance.address:
                response_object['address'] = PatientAddressSerializer(instance.address).data
            if instance.phlebo:
                response_object['phlebo'] = PhleboSerializer(instance.phlebo).data
            
            if instance.prescription:
                response_object['prescription'] = generate_pre_signed_url(
                    instance.prescription.url)
        except Exception as error:
            logger.error("Exception in LabTestAppointmentSerializer %s"%(str(error)))
            response_object['prescription'] = None
        
        return response_object
    
class HospitalRegionSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = HospitalRegion
        fields = '__all__'
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.health_test:
            response_object['health_test'] = HomeCareHealthTestSerializer(instance.health_test).data
        return response_object
    
class LabTestSlotsMasterSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = LabTestSlotsMaster
        fields = '__all__'
        
class LabTestSlotsWeeklyMasterSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = LabTestSlotsWeeklyMaster
        fields = '__all__'
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.health_test:
            response_object['health_test'] = HomeCareHealthTestSerializer(instance.health_test).data
        if instance.slot:
            response_object['slot'] = LabTestSlotsMasterSerializer(instance.slot).data
        
        return response_object
    
class LabTestSlotScheduleSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = LabTestSlotSchedule
        fields = '__all__'
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.hospital:
                response_object['hospital'] = HospitalSerializer(instance.hospital).data
        if instance.weekly_slot:
            response_object['weekly_slot'] = LabTestSlotsWeeklyMasterSerializer(instance.weekly_slot).data
        if instance.phlebo:
            response_object['phlebo'] = PhleboSerializer(instance.phlebo).data
        
        return response_object
    
class LabAppointmentHistorySerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = LabTestAppointmentHistory
        fields = '__all__'
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.appointment:
                response_object['appointment'] = LabTestAppointmentSerializer(instance.appointment).data
        if instance.phlebo:
            response_object['phlebo'] = PhleboSerializer(instance.phlebo).data
        
        return response_object

                                                                                           
    
