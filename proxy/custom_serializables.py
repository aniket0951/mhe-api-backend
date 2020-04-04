class ValidateUHID:
    def __init__(self, uhid=None, otp=None):
        self.uhid = uhid
        self.otp = otp

    def serialize(self, serializer):
        serializer.start_object('ValidateRequestParam')
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('POTP', self.otp)


class SlotAvailability:
    def __init__(self, doctor_code=None, location_code=None, schedule_date=None, appointment_type=None, speciality_code=None, p_discount_amount="1"):
        self.doctor_code = doctor_code
        self.location_code = location_code
        self.schedule_date = schedule_date
        self.appointment_type = appointment_type
        self.speciality_code = speciality_code
        self.p_discount_amount = p_discount_amount

    def serialize(self, serializer):
        serializer.start_object('DoctorParam')
        serializer.add_property('doctorCode', self.doctor_code)
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('scheduleDate', self.schedule_date)
        serializer.add_property('specialtyCode', self.speciality_code)
        serializer.add_property('pdiscountAmount', self.p_discount_amount)


class CancelAppointmentRequest:
    def __init__(self, appointment_identifier=None, location_code=None):
        self.appointment_identifier = appointment_identifier
        self.location_code = location_code

    def serialize(self, serializer):
        serializer.start_object('CancelAppointments')
        serializer.add_property('appointmentIdentifier',
                                self.appointment_identifier)
        serializer.add_property('locationCode', self.location_code)


class BookMySlot:
    def __init__(self, param):
        self.doctor_code = param.get("doctor_code", None)
        self.mrn = param.get("mrn", None)
        self.appointment_date_time = param.get("appointment_date_time", None)
        self.location_code = param.get("location_code", None)
        self.patient_name = param.get("patient_name", None)
        self.mobile = param.get("mobile", None)
        self.email = param.get("email", None)
        self.duration = param.get("duration", "10")
        self.visit_type = param.get("visit_type", "A")
        self.appointment_type = param.get("appointment_type", "NEW")
        self.reason_for_visit = param.get("reason_for_visit", "CONSULT")
        self.fast_care_id = param.get("fast_care_id", "PatientApp")
        self.speciality_code = param.get("speciality_code", None)

    def serialize(self, serializer):
        serializer.start_object('IbookAppointmentParam')
        serializer.add_property('doctorCode', self.doctor_code)
        serializer.add_property('appointmentDateTime',
                                self.appointment_date_time)
        serializer.add_property('mrn', self.mrn)
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('patientName', self.patient_name)
        serializer.add_property('mobile', self.mobile)
        serializer.add_property('email', self.email)
        serializer.add_property('duration', self.duration)
        serializer.add_property('visitType', self.visit_type)
        serializer.add_property('appointmentType', self.appointment_type)
        serializer.add_property('reasonForVisitCode', self.reason_for_visit)
        serializer.add_property('fastCareID', self.fast_care_id)
        serializer.add_property('specialtyCode', self.speciality_code)


class SyncAPIRequest:
    def __init__(self, location_code=None, sync_method=None):
        self.location_code = location_code
        self.sync_method = sync_method

    def serialize(self, serializer):
        serializer.start_object('SyncRequestParam')
        serializer.add_property('SyncLocationCode', self.location_code)
        serializer.add_property('SyncMethod', self.sync_method)


class ItemTariffPrice:
    def __init__(self, location_code=None, sync_method='tariff', item_code=None):
        self.location_code = location_code
        self.sync_method = sync_method
        self.item_code = item_code

    def serialize(self, serializer):
        serializer.start_object('SyncRequestParam')
        serializer.add_property('SyncLocationCode', self.location_code)
        serializer.add_property('SyncMethod', self.sync_method)
        serializer.add_property('SyncItemCode', self.item_code)


class DoctorSchedule:
    def __init__(self, doctor_code=None, location_code=None, department_code=None):
        self.doctor_code = doctor_code
        self.location_code = location_code
        self.department_code = department_code

    def serialize(self, serializer):
        serializer.start_object('weeklyScheduleParam')
        serializer.add_property('DoctorCode',
                                self.doctor_code)
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('DepartmentCode', self.department_code)


class CreateUHID:
    def __init__(self, param):
        self.title_id = param.get("title_id", None)
        self.first_name = param.get("first_name", None)
        self.middle_name = param.get("middle_name", None)
        self.last_name = param.get("last_name", None)
        self.last_name = param.get("last_name", None)
        self.marital_status_id = param.get("marital_status_id", None)
        self.dob = param.get("dob", None)
        self.phone_no = param.get("phone_no", None)
        self.email = param.get("email", None)
        self.national_id = param.get("national_id", None)
        self.address = param.get("address", None)
        self.city_area_id = param.get("city_area_id", None)
        self.city_id = param.get("city_id", None)
        self.zip_code = param.get("zip_code", None)
        self.hospital_id = param.get("hospital_id", None)
        self.gender_id = param.get("gender_id", None)
        self.age = param.get("age", None)
        self.sms_alert = param.get("sms_alert", None)
        self.email_alert = param.get("email_alert", None)
        self.country = param.get("country", None)
        self.state = param.get("state", None)
        self.parent_spouse = param.get("parent_spouse", None)
        self.par_spouse_mob_no = param.get("par_spouse_mob_no", None)
        self.emr_contact_name = param.get("emr_contact_name", None)
        self.emr_contact_no = param.get("emr_contact_no", None)
        self.religion = param.get("religion", None)
        self.payment_type = param.get("payment_type", None)
        self.id_proof_name = param.get("id_proof_name", None)
        self.id_no = param.get("id_no", None)
        self.nok_name = param.get("nok_name", None)
        self.nok_contact_number = param.get("nok_contact_number", None)
        self.nok_relation = param.get("nok_relation", None)
        self.passport_no = param.get("passport_no", None)
        self.passport_issue_date = param.get("passport_issue_date", None)
        self.passport_expiry_date = param.get("passport_expiry_date", None)

    def serialize(self, serializer):
        serializer.start_object('PreRegparam')
        serializer.add_property('TitleID', self.title_id)
        serializer.add_property('FirstName', self.first_name)
        serializer.add_property('MiddleName', self.middle_name)
        serializer.add_property('LastName', self.last_name)
        serializer.add_property('GenderID', self.gender_id)
        serializer.add_property('MaritalStatusID', self.marital_status_id)
        serializer.add_property('DOB', self.dob)
        serializer.add_property('PhoneNo', self.phone_no)
        serializer.add_property('EMail', self.email)
        serializer.add_property('NationalID', self.national_id)
        serializer.add_property('Address', self.address)
        serializer.add_property('CityAreaID', self.city_area_id)
        serializer.add_property('CityID', self.city_id)
        serializer.add_property('ZipCode', self.zip_code)
        serializer.add_property('HospitalID', self.hospital_id)
        serializer.add_property('Age', self.age)
        serializer.add_property('SmsAlert', self.sms_alert)
        serializer.add_property('EmailAlert', self.email_alert)
        serializer.add_property('Country', self.country)
        serializer.add_property('State', self.state)
        serializer.add_property('ParentSpouse', self.parent_spouse)
        serializer.add_property('ParSpouseMobno', self.par_spouse_mob_no)
        serializer.add_property('EMRContName', self.emr_contact_name)
        serializer.add_property('EMRContMobNo', self.emr_contact_no)
        serializer.add_property('Religion', self.religion)
        serializer.add_property('PaymentType', self.payment_type)
        serializer.add_property('IDProofName', self.id_proof_name)
        serializer.add_property('IDNo', self.id_no)
        serializer.add_property('NOKname', self.nok_name)
        serializer.add_property('NOKContactno', self.nok_contact_number)
        serializer.add_property('NOKrelation', self.nok_relation)
        serializer.add_property('PassportNo', self.passport_no)
        serializer.add_property('PassportIssueDate', self.passport_issue_date)
        serializer.add_property('PassportExpiryDate',
                                self.passport_expiry_date)


class IPBills:
    def __init__(self, location_code=None, uhid=None):
        self.location_code = location_code
        self.uhid = uhid

    def serialize(self, serializer):
        serializer.start_object('DepositAmtParam')
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('LocationCode', self.location_code)


class OPBills:
    def __init__(self, location_code=None, uhid=None):
        self.location_code = location_code
        self.uhid = uhid

    def serialize(self, serializer):
        serializer.start_object('PatOutStandAmtParam')
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('LocationCode', self.location_code)


class EpisodeItems:
    def __init__(self, location_code=None, admission_no=None):
        self.location_code = location_code
        self.admission_no = admission_no

    def serialize(self, serializer):
        serializer.start_object('GetEpisodeItemsParam')
        serializer.add_property('AdmNo', self.admission_no)
        serializer.add_property('LocationCode', self.location_code)

class NextAvailableSlot:
    def __init__(self, doctor_code=None, location_code=None, schedule_date=None, department_code=None):
        self.doctor_code = doctor_code
        self.location_code = location_code
        self.schedule_date = schedule_date
        self.department_code = department_code

    def serialize(self, serializer):
        serializer.start_object('NextAvailableSlotDateParam')
        serializer.add_property('doctorCode', self.doctor_code)
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('scheduleDate', self.schedule_date)
        serializer.add_property('departmentCode', self.department_code)
