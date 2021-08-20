from apps.doctors.serializers import DoctorsWeeklyScheduleSerializer
from apps.doctors.models import DoctorsWeeklySchedule
import ast
import json
import logging
from apps.doctors.constants import DoctorsConstants
from datetime import datetime
from rest_framework.test import APIClient


client = APIClient()
logger = logging.getLogger("django")

def process_slots(slots):
    morning_slot, afternoon_slot, evening_slot = [], [], []
    if slots:
        slot_list = ast.literal_eval(slots)
        for slot in slot_list:
            appointment_type = "HV"
            if "HVVC" in slot['startTime']:
                time_format = '%d %b, %Y %I:%M:%S %p(HVVC)'
                appointment_type = "HVVC"
            elif "VC" in slot['startTime']:
                time_format = '%d %b, %Y %I:%M:%S %p(VC)'
                appointment_type = "VC"
            elif "PR" in slot['startTime']:
                time_format = '%d %b, %Y %I:%M:%S %p(PR)'
                appointment_type = "PR"
            else:
                time_format = '%d %b, %Y %I:%M:%S %p(HV)'
            time = datetime.strptime(
                slot['startTime'], time_format).time()
            if time.hour < 12:
                morning_slot.append({"slot": time.strftime(DoctorsConstants.APPOINTMENT_SLOT_TIME_FORMAT), "type": appointment_type})
            elif (time.hour >= 12) and (time.hour < 17):
                afternoon_slot.append({"slot": time.strftime(DoctorsConstants.APPOINTMENT_SLOT_TIME_FORMAT), "type": appointment_type})
            else:
                evening_slot.append({"slot": time.strftime(DoctorsConstants.APPOINTMENT_SLOT_TIME_FORMAT), "type": appointment_type})
    return morning_slot, afternoon_slot, evening_slot

def get_doctor_weekly_schedule_from_mainpal(location_code,department_code,doctor_code):
    weekly_schedule_data = None
    try:
        response        = client.post('/api/doctors/schedule',json.dumps({
                                                            'location_code': location_code, 
                                                            'department_code': department_code, 
                                                            'doctor_code': doctor_code,
                                                        }), content_type='application/json')
        if response.status_code == 200 and response.data["success"] == True:
            weekly_schedule_data = response.data["data"]
    except Exception as e:
            logger.error("Unexpected error occurred while calling the API- {0}".format(e))
    return weekly_schedule_data

def get_and_update_doctors_weekly_schedule(doctor_instance):
    
    all_departments = doctor_instance.hospital_departments.all()

    for each_department in all_departments:
            
        hospital_descrption = doctor_instance.hospital.descrption
        hospital_code       = doctor_instance.hospital.code
        department_code     = each_department.department.code
        doctor_code         = doctor_instance.code

        try:

            weekly_schedule_response = get_doctor_weekly_schedule_from_mainpal(
                                                                    hospital_code,
                                                                    department_code,
                                                                    doctor_code
                                                                )
            if weekly_schedule_response and weekly_schedule_response.get(hospital_descrption):

                recently_updated = []

                for weekly_schedule_data in weekly_schedule_response.get(hospital_descrption):

                    data = dict()
                    data["doctor"]      = doctor_instance.id
                    data["department"]  = each_department.department.id
                    data["hospital"]    = doctor_instance.hospital.id
                    data["day"]         = weekly_schedule_data["Date"]
                    data["from_time"]   = datetime.strptime(weekly_schedule_data["From-Time"], "%I:%M%p").time()
                    data["to_time"]     = datetime.strptime(weekly_schedule_data["To-Time"], "%I:%M%p").time()
                    data["serivce"]     = weekly_schedule_data["SessionType"]

                    weekly_schedule = DoctorsWeeklySchedule.objects.filter(
                                                doctor__code=doctor_code,
                                                department__code=each_department.department.code,
                                                day=data["day"],
                                                from_time=data["from_time"],
                                                to_time=data["to_time"],
                                                serivce=data["serivce"]
                                            ).first()
                    if weekly_schedule:
                        serializer = DoctorsWeeklyScheduleSerializer(weekly_schedule, data=data, partial=True)
                    else:
                        serializer = DoctorsWeeklyScheduleSerializer(data=data)
                            
                    serializer.is_valid(raise_exception=True)
                    weekly_schedule_object = serializer.save()

                    recently_updated.append(weekly_schedule_object.id)

                weekly_schedule = DoctorsWeeklySchedule.objects.filter(
                                                doctor__code=doctor_code,
                                                department__code=department_code,
                                                hospital__code=hospital_code,
                                            ).exclude(
                                                id__in=recently_updated
                                            ).delete()

        except Exception as e:
                logger.error("Unexpected error occurred while processing the API response- {0}".format(e))