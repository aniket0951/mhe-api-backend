from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
from rest_framework.response import Response
from apps.doctors.models import Doctor
from apps.doctors.serializers import DoctorSerializer

# @api_view(['GET'])
# def base(request):
#     return render(request, "question_answer/base.html")

@api_view(['GET'])
def appointment(request):
    doctors = Doctor.objects.all()
    serializer = DoctorSerializer(doctors, many=True)
    return JsonResponse(serializer.data, safe=False)
from django.shortcuts import render

# Create your views here.
