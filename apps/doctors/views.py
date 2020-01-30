from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.core import serializers
import json
from django.db.models import Q
from django.forms.models import model_to_dict
from rest_framework.response import Response
from apps.doctors.models import Doctor
from apps.master_data.models import Hospital, Specialisation
from apps.doctors.serializers import DoctorSerializer, HospitalDetailSerializer, SpecialisationDetailSerializer,SpecialisationDetailSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework import generics
from rest_framework import filters


"""
class DoctorViewSet(ModelViewset):
    serializer_class = DoctorSerializer
    queryset = Doctor.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['specialisations', 'linked_hospitals']

    def get_queryset(self):
        queryset = Doctor.objects.filter(specialisations__code = 'dmc' , linked_hospitals__code = 'whf')
        return queryset


"""
class DoctorsAPIView(generics.ListCreateAPIView):
    
    search_fields = ['specialisations__code', 'first_name', 'linked_hospitals__profit_center']
    filter_backends = (filters.SearchFilter,)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    """
    def get_queryset(self):
        qs = super().get_queryset() 
        location = self.request.GET.get('location')
        return qs.filter(linked_hospitals__code = location)
    """
class LocationAPIView(generics.ListCreateAPIView):
    queryset          = Hospital.objects.all()
    serializer_class  = HospitalDetailSerializer

class SpecialisationAPIView(generics.ListCreateAPIView):
    queryset          = Specialisation.objects.all()
    serializer_class  = SpecialisationDetailSerializer
"""
class DoctorDetailAPIView(generics.RetrieveAPIView):
    
    queryset          = Doctor.objects.all()
    serializer_class  = DoctorDetailSerializer
    
    def get(self, request, pk, *args, **kwargs):
        doctor = Doctor.objects.get(pk=pk)
        serializer = SpecialisationDetailSerializer(doctor)
        return Response(serializer.data)
"""

@api_view(['GET'])
def DoctorDetailView(request):
    data = request.query_params
    code = data.get("code")
    date = data.get("date")
    hospital_code = data.get("hospital_code")
    specialisation_code = data.get("specialisation_code")
    results = Doctor.objects.filter(code = code, linked_hospitals__profit_center = hospital_code, specialisations__code = specialisation_code).filter(Q(end_date__gte = date) | Q(end_date__isnull=True))
    tmpJson = serializers.serialize("json",results)
    tmpObj = json.loads(tmpJson)
    if(len(tmpObj) == 0):
        return Response("Doctor is not available on this date")
    json_to_be_returned = tmpObj[0]

    """
    Call API for available slot and store all the slots in below Variable
    """
    json_to_be_returned["available_slot"] = ["5:50- 6:50", "7:50- 9:50"]
    return HttpResponse(json.dumps(json_to_be_returned))


@api_view(['POST'])
def bookAppointment(request):
    pass

    

    
    
    



    
    
    
    

    