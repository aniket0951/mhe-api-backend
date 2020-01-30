from django.shortcuts import render
from .models import Appointment
from .serializers import AppointmentSerializer

# Create your views here.
import rest_framework
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import filters
from rest_framework.decorators import api_view
from apps.doctors.models import Doctor
from apps.master_data.models import Hospital
from apps.patients.models import Patient


"""
class AppointmentViewSet(viewsets.ModelViewSet):
    
    retrieve:
    Return the given Appointment.    
    
    list:
    Return a list of all the existing Appointments.    
    
    create:
    Create a new Appointment instance.
    
    queryset = Appointment.objects.all()
    serializer_class = Appointment
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    ordering_fields = '__all__'
     
    
    def get_serializer_class(self):
        
        Determins which serializer to user `list` or `detail`
        
        if self.action == 'retrieve':
            if hasattr(self , 'detail_serializer_class'):
                return self.detail_serializer_class
        return super().get_serializer_class()
    

    def get_queryset(self):
        
        Optionally restricts the returned queries by filtering against
        patient, hospital, Doctor  query parameter in the URL.
        
        queryset = Appointment.objects.all()
        patient = self.request.query_params.get('patient', None)
        hospital = self.request.query_params.get('hospital', None)
        doctor = self.request.query_params.get('doctor', None)
        if patient is not None:
            patient_name = patient.name
            queryset = queryset.filter(name = patient_name)
        if hospital is not None:
            hospital_name = hospital.description
            queryset = queryset.filter(description = hospital_name)
        if doctor is not None:
            doctor_name = doctor.name
            queryset = queryset.filter(name = doctor_name)
        return queryset
"""

class AppointmentsAPIView(generics.ListCreateAPIView):
    search_fields = ['patient__first_name', 'doctor__first_name', 'hospital__profit_center']
    filter_backends = (filters.SearchFilter,)
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        queryset = Appointment.objects.all()
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id is not None:
            queryset = queryset.filter(patient_id = patient_id)
            return queryset


@api_view(['POST'])
def CreateAppointment(request):
    data = request.data
    patient_id = data.get("patient_id")
    hospital_id = data.get("hospital_id")
    doctor_id = data.get("doctor_id")
    slot = data.get("slot")
    appointment_date = data.get("appintment_date")
    doctor = Doctor.objects.filter(first_name = doctor_id).first()
    patient = Patient.objects.filter(unique_identifier = patient_id).first()
    print(patient)
    hospital = Hospital.objects.filter(code = hospital_id).first()

    """
    Call the Booking API  here and get all the status and create a entry in Database

    """

    appointment = Appointment(appointment_date= appointment_date ,time_slot_from = slot, token_no = 7, status= 1, patient = patient , doctor = doctor ,hospital = hospital)
    appointment.save()
    return Response("Appointment has been created", status=200)

@api_view(['POST'])
def CancelAppointment(request):
    data = request.data
    appointment_id = data.get("appointment_id")
    print(appointment_id)
    instance = Appointment.objects.filter(id = appointment_id).first()
    """
    Call the API for cancellation and once confirm update the record
    """
    instance.status = 2
    instance.save()
    return Response({"message": "Appointment has been cancelled"}, status = 2)


      
        
        


