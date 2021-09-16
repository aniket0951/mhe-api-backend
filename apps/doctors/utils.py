import ast

import logging
from apps.doctors.constants import DoctorsConstants
from datetime import date, datetime
from rest_framework.test import APIClient


client = APIClient()
logger = logging.getLogger("django")

def process_slots(slots):
    morning_slot, afternoon_slot, evening_slot = [], [], []
    services = {"HV":False,"VC":False,"PR":False}
    if slots:
        slot_list = ast.literal_eval(slots)
        for slot in slot_list:
            appointment_type = "HV"
            end_time_format = '%d %b, %Y %I:%M:%S %p'

            if "HVVC" in slot['startTime']:
                time_format = '%d %b, %Y %I:%M:%S %p(HVVC)'
                appointment_type = "HVVC"
                services["HV"] = True
                services["VC"] = True
            elif "VC" in slot['startTime']:
                time_format = '%d %b, %Y %I:%M:%S %p(VC)'
                appointment_type = "VC"
                services["VC"] = True
            elif "PR" in slot['startTime']:
                time_format = '%d %b, %Y %I:%M:%S %p(PR)'
                appointment_type = "PR"
                services["PR"] = True
            else:
                time_format = '%d %b, %Y %I:%M:%S %p(HV)'
                services["HV"] = True
            time = datetime.strptime(
                slot['startTime'], time_format).time()
            end_time = datetime.strptime(slot['endTime'], end_time_format).time()
        
            slot_duration_td = datetime.combine(date.today(), end_time) - datetime.combine(date.today(), time)
            slot_duration_minute = (slot_duration_td.seconds//60)%60   
         
            if time.hour < 12:
                morning_slot.append({"slot": time.strftime(DoctorsConstants.APPOINTMENT_SLOT_TIME_FORMAT), "type": appointment_type, 'slot_duration':slot_duration_minute})
            elif (time.hour >= 12) and (time.hour < 17):
                afternoon_slot.append({"slot": time.strftime(DoctorsConstants.APPOINTMENT_SLOT_TIME_FORMAT), "type": appointment_type, 'slot_duration':slot_duration_minute})
            else:
                evening_slot.append({"slot": time.strftime(DoctorsConstants.APPOINTMENT_SLOT_TIME_FORMAT), "type": appointment_type, 'slot_duration':slot_duration_minute})
    return morning_slot, afternoon_slot, evening_slot, services