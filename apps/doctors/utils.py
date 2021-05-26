import ast
from apps.doctors.constants import DoctorsConstants
from datetime import datetime

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