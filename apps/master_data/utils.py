import logging
from datetime import datetime
from .constants import MasterDataConstants

from apps.doctors.views import DoctorScheduleView
from apps.notifications.utils import cancel_parameters
from apps.doctors.serializers import DoctorsWeeklyScheduleSerializer
from apps.doctors.models import DoctorsWeeklySchedule

logger = logging.getLogger("django")

class MasterDataUtils:

    @staticmethod
    def process_department_details(each_department,department_sorted_keys):

        department_details = dict()

        for index, key in enumerate(sorted(each_department.keys())):
            if not each_department[key]:
                each_department[key] = None

            if key in ['DateFrom', 'DateTo'] and each_department[key]:
                each_department[key] = datetime.strptime(
                    each_department[key], '%d/%m/%Y').strftime(MasterDataConstants.DATE_FORMAT)

            department_details[department_sorted_keys[index]] = each_department[key]
        
        return department_details

    @staticmethod
    def process_lab_and_radiology_items(each_lab_radiology_item,lab_radiology_items_sorted_keys):
        hospital_lab_radiology_item_details = dict()
        for index, key in enumerate(sorted(each_lab_radiology_item.keys())):
            if not each_lab_radiology_item[key]:
                each_lab_radiology_item[key] = None
            if key in ['DateFrom', 'DateTo'] and each_lab_radiology_item[key]:
                each_lab_radiology_item[key] = datetime.strptime(each_lab_radiology_item[key], '%d/%m/%Y').strftime(MasterDataConstants.DATE_FORMAT)
            if key == 'ItemDesc' and each_lab_radiology_item[key]:
                each_lab_radiology_item[key] = each_lab_radiology_item[key].title()
            hospital_lab_radiology_item_details[lab_radiology_items_sorted_keys[index]] = each_lab_radiology_item[key]
        return each_lab_radiology_item, hospital_lab_radiology_item_details

    @staticmethod
    def get_doctor_weekly_schedule_from_mainpal(location_code,department_code,doctor_code):
        weekly_schedule_data = None
        try:
            param = {
                'location_code': location_code, 
                'department_code': department_code, 
                'doctor_code': doctor_code,
            }
            request_param = cancel_parameters(param)
            response = DoctorScheduleView.as_view()(request_param)
            if response.status_code == 200 and response.data["success"] == True:
                weekly_schedule_data = response.data["data"]
        except Exception as e:
                logger.error("Unexpected error occurred while calling the API- {0}".format(e))
        return weekly_schedule_data

    @staticmethod
    def get_and_update_doctors_weekly_schedule(doctor_instance):
        
        all_departments = doctor_instance.hospital_departments.all()

        for each_department in all_departments:
                
            hospital_description = doctor_instance.hospital.description
            hospital_code       = doctor_instance.hospital.code
            department_code     = each_department.department.code
            doctor_code         = doctor_instance.code

            try:

                weekly_schedule_response = MasterDataUtils.get_doctor_weekly_schedule_from_mainpal(
                                                                        hospital_code,
                                                                        department_code,
                                                                        doctor_code
                                                                    )
                
                if weekly_schedule_response and weekly_schedule_response.get(hospital_description):

                    recently_updated = []

                    for weekly_schedule_data in weekly_schedule_response.get(hospital_description):

                        data = dict()
                        data["doctor"]      = doctor_instance.id
                        data["department"]  = each_department.department.id
                        data["hospital"]    = doctor_instance.hospital.id
                        data["day"]         = weekly_schedule_data["Date"]
                        data["from_time"]   = datetime.strptime(weekly_schedule_data["From-Time"], "%I:%M%p").time()
                        data["to_time"]     = datetime.strptime(weekly_schedule_data["To-Time"], "%I:%M%p").time()
                        data["service"]     = weekly_schedule_data["SessionType"]

                        weekly_schedule = DoctorsWeeklySchedule.objects.filter(
                                                    doctor__code=doctor_code,
                                                    department__code=department_code,
                                                    day=data["day"],
                                                    from_time=data["from_time"],
                                                    to_time=data["to_time"],
                                                    service=data["service"]
                                                ).first()
                        if weekly_schedule:
                            serializer = DoctorsWeeklyScheduleSerializer(weekly_schedule, data=data, partial=True)
                        else:
                            serializer = DoctorsWeeklyScheduleSerializer(data=data)
                                
                        serializer.is_valid(raise_exception=True)
                        weekly_schedule_object = serializer.save()

                        recently_updated.append(weekly_schedule_object.id)

                    delete_older_weekly_schedules = DoctorsWeeklySchedule.objects.filter(
                                                    doctor__code=doctor_code,
                                                    department__code=department_code,
                                                    hospital__code=hospital_code,
                                                ).exclude(
                                                    id__in=recently_updated
                                                )
                    delete_older_weekly_schedules.delete()

            except Exception as e:
                    logger.error("Unexpected error occurred while processing the API response- {0}".format(e))