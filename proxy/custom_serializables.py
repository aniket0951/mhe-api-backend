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
    def __init__(self, doctor_code=None, appointment_date_time=None, mrn=None, location_code=None,
                 patient_name=None, mobile=None, email=None, duration="10", visit_type="A",
                 appointment_type="NEW", reason_for_visit="CONSULT", fast_care_id="PatientApp",
                 speciality_code=None):
        self.doctor_code = doctor_code
        self.mrn = mrn
        self.appointment_date_time = appointment_date_time
        self.location_code = location_code
        self.patient_name = patient_name
        self.mobile = mobile
        self.email = email
        self.duration = duration
        self.visit_type = visit_type
        self.appointment_type = appointment_type
        self.reason_for_visit = reason_for_visit
        self.fast_care_id = fast_care_id
        self.speciality_code = speciality_code

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
    def __init__(self, doctor_code=None, location_code=None, department_code = None):
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
    def __init__(self, title_id =None, first_name=None,middle_name = None ,last_name=None, gender_id=None, 
                 marital_status_id=None, dob=None, phone_no =None, email=None, national_id=None, 
                 address=None, city_area_id=None, city_id=None, zip_code=None,hospital_id=None,
                 age=None,sms_alert="1",email_alert = "1",country = None, state = None, parent_spouse = "1",
                 par_spouse_mob_no = "1", emr_contact_name = None, emr_contact_no = None, religion = None,
                  payment_type = None, id_proof_name = None, id_no = None, nok_name = None,
                  nok_contact_number = None, nok_relation = None,passport_no = None, 
                  passport_issue_date=None, passport_expiry_date = None):
        self.title_id = title_id
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.gender_id = gender_id
        self.marital_status_id = marital_status_id
        self.dob = dob
        self.phone_no = phone_no
        self.email = email
        self.national_id = national_id
        self.address = address
        self.city_area_id = city_area_id
        self.city_id = city_id
        self.zip_code = zip_code
        self.hospital_id = hospital_id
        self.age = age
        self.sms_alert = sms_alert
        self.email_alert = email_alert
        self.country = country
        self.state = state
        self.parent_spouse = parent_spouse
        self.par_spouse_mob_no = par_spouse_mob_no
        self.emr_contact_name = emr_contact_name
        self.emr_contact_no = emr_contact_no
        self.religion = religion
        self.payment_type = payment_type
        self.id_proof_name = id_proof_name
        self.id_no = id_no
        self.nok_name = nok_name
        self.nok_contact_number = nok_contact_number
        self.nok_relation = nok_relation
        self.passport_no = passport_no
        self.passport_issue_date = passport_issue_date
        self.passport_expiry_date = passport_expiry_date

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
        serializer.add_property('PassportExpiryDate', self.passport_expiry_date)

class PayBills:
    def __init__(self, location_code=None, uhid = None):
        self.location_code = location_code
        self.uhid = uhid

    def serialize(self, serializer):
        serializer.start_object('DepositAmtParam')
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('LocationCode', self.location_code)
        





