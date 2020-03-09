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
