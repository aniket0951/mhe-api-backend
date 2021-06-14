class ValidateUHID:
    def __init__(self, uhid=None, otp=None):
        self.uhid = uhid
        self.otp = otp

    def serialize(self, serializer):
        serializer.start_object('ValidateRequestParam')
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('POTP', self.otp)
        serializer.add_property('LocationCode', "MHB")


class PatientDetails:
    def __init__(self,mobile=None,location_code=None,check_code=None):
        self.mobile = mobile
        self.location_code = location_code
        self.check_code = check_code
    def serialize(self, serializer):
        serializer.start_object('patdetailParammn')
        serializer.add_property('mobileno', self.mobile)
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('checkcode',self.check_code)


class SlotAvailability:
    def __init__(self, doctor_code=None, location_code=None, schedule_date=None,
                 appointment_type=None, speciality_code=None):
        self.doctor_code = doctor_code
        self.location_code = location_code
        self.schedule_date = schedule_date
        self.appointment_type = appointment_type
        self.speciality_code = speciality_code
        self.p_discount_amount = "1"
        self.source = "patientapp"

    def serialize(self, serializer):
        serializer.start_object('DoctorParam')
        serializer.add_property('doctorCode', self.doctor_code)
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('scheduleDate', self.schedule_date)
        serializer.add_property('specialtyCode', self.speciality_code)
        serializer.add_property('pdiscountAmount', self.p_discount_amount)
        serializer.add_property('source', self.source)


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
        self.slot_type = param.get("appointment_mode", None)
        self.dob = param.get("dob", None)

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
        serializer.add_property('slottype', self.slot_type)
        serializer.add_property('dateofbirth', self.dob)


class SyncAPIRequest:
    def __init__(self, location_code=None, sync_method=None, item_code=None):
        self.location_code = location_code
        self.sync_method = sync_method
        self.item_code = item_code

    def serialize(self, serializer):
        serializer.start_object('SyncRequestParam')
        serializer.add_property('SyncLocationCode', self.location_code)
        serializer.add_property('SyncMethod', self.sync_method)
        serializer.add_property('SyncItemCode', self.item_code)


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
        self.language = param.get("language", None)
        self.locality = param.get("locality", None)

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
        serializer.add_property('language', self.language)
        serializer.add_property('locality', self.locality)


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
    def __init__(self, doctor_code=None, location_code=None, schedule_date=None,
                 department_code=None, app_type=None):
        self.doctor_code = doctor_code
        self.location_code = location_code
        self.schedule_date = schedule_date
        self.department_code = department_code
        self.app_type = app_type

    def serialize(self, serializer):
        serializer.start_object('NextAvailableSlotDateParam')
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('departmentCode', self.department_code)
        serializer.add_property('doctorCode', self.doctor_code)
        serializer.add_property('scheduleDate', self.schedule_date)
        serializer.add_property('AppType', self.app_type)


class UpdateCancelAndRefund:
    def __init__(self, param):
        self.app_id = param.get("app_id", None)
        self.cancel_remark = param.get("cancel_remark", None)
        self.refund_amount = param.get("refund_amount", None)
        self.refund_trans_id = param.get("refund_trans_id", None)
        self.refund_date = param.get("refund_date", None)
        self.refund_time = param.get("refund_time", None)
        self.refund_status = param.get("refund_status", None)
        self.location_code = param.get("location_code", None)

    def serialize(self, serializer):
        serializer.start_object('UpdateAppParam')
        serializer.add_property('AppId', self.app_id)
        serializer.add_property('CancelRemark', self.cancel_remark)
        serializer.add_property('RefundAmt', self.refund_amount)
        serializer.add_property('RefundTransId', self.refund_trans_id)
        serializer.add_property('RefundDate', self.refund_date)
        serializer.add_property('RefundTime', self.refund_time)
        serializer.add_property('RefundStatus', self.refund_status)
        serializer.add_property('locationCode', self.location_code)


class UpdateRebookStatus:
    def __init__(self, param):
        self.app_id = param.get("app_id", None)
        self.package_code = param.get("package_code", None)
        self.type = param.get("type", None)
        self.total_amount = param.get("total_amount", None)
        self.receipt_no = param.get("receipt_no", None)
        self.trans_id = param.get("trans_id", None)
        self.location_code = param.get("location_code", None)

    def serialize(self, serializer):
        serializer.start_object('RebookAppParam')
        serializer.add_property('AppId', self.app_id)
        serializer.add_property('PkagCode', self.package_code)
        serializer.add_property('Type', self.type)
        serializer.add_property('TotAmt', self.total_amount)
        serializer.add_property('ReceiptNo', self.receipt_no)
        serializer.add_property('Transid', self.trans_id)
        serializer.add_property('locationCode', self.location_code)


class RescheduleAppointment:
    def __init__(self, app_id=None, location_code=None, new_date=None, app_type=None):
        self.app_id = app_id
        self.location_code = location_code
        self.new_date = new_date
        self.app_type = app_type

    def serialize(self, serializer):
        serializer.start_object('ReScheduleAppParam')
        serializer.add_property('AppId', self.app_id)
        serializer.add_property('newdate', self.new_date)
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('AppType', self.app_type)


class SendVcStatus:
    def __init__(self, app_id=None, location_code=None, set_status=None):
        self.app_id = app_id
        self.location_code = location_code
        self.set_status = set_status

    def serialize(self, serializer):
        serializer.start_object('VCStatusSetParam')
        serializer.add_property('AppointmentId', self.app_id)
        serializer.add_property('SetStatus', self.set_status)
        serializer.add_property('locationCode', self.location_code)


class DoctotLogin:
    def __init__(self, user_id=None, pwd=None, location_code=None):
        self.user_id = user_id
        self.pwd = pwd
        self.location_code = location_code
        self.checksum = None

    def serialize(self, serializer):
        serializer.start_object('loginParam')
        serializer.add_property('userid', self.user_id)
        serializer.add_property('pwd', self.pwd)
        serializer.add_property('checksum', self.checksum)
        serializer.add_property('locationCode', self.location_code)


class RescheduleSlot:
    def __init__(self, doctor_code=None, location_code=None, schedule_date=None,
                 appointment_type=None, speciality_code=None):
        self.doctor_code = doctor_code
        self.location_code = location_code
        self.schedule_date = schedule_date
        self.appointment_type = appointment_type
        self.speciality_code = speciality_code
        self.source = "patientapp"

    def serialize(self, serializer):
        serializer.start_object('SlotParam')
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('specialtyCode', self.speciality_code)
        serializer.add_property('doctorCode', self.doctor_code)
        serializer.add_property('scheduleDate', self.schedule_date)
        serializer.add_property('source', self.source)
        serializer.add_property('appointmentType', self.appointment_type)


class DoctorConsultationCharges:
    def __init__(self, 
        location_code=None, 
        specialty_code=None, 
        doctor_code=None,
        promo_code=None,
    ):
        self.location_code = location_code
        self.specialty_code = specialty_code
        self.doctor_code = doctor_code
        self.promo_code = promo_code

    def serialize(self, serializer):
        serializer.start_object('consultchargesParam')
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('specialtyCode', self.specialty_code)
        serializer.add_property('doctorCode', self.doctor_code)
        serializer.add_property('PromoCode', self.promo_code)


class CurrentPatientList:
    def __init__(self, location_code=None, specialty_code=None, doctor_code=None, visit_type='IP'):
        self.location_code = location_code
        self.specialty_code = specialty_code
        self.doctor_code = doctor_code
        self.visit_type = visit_type

    def serialize(self, serializer):
        serializer.start_object('CurrentPatientsParam')
        serializer.add_property('LocationCode', self.location_code)
        serializer.add_property('DepartmentCode', self.specialty_code)
        serializer.add_property('DoctorCode', self.doctor_code)
        serializer.add_property('VisitType', self.visit_type)


class HealthPackagePrice:
    def __init__(self, location_code=None, package_code=None, uhid="NA", promo_code="NA"):
        self.location_code = location_code
        self.package_code = package_code
        self.uhid = uhid
        self.promo_code = promo_code

    def serialize(self, serializer):
        serializer.start_object('packagepriceParam')
        serializer.add_property('packageCode', self.package_code)
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('PromoCode', self.promo_code)



class CurrentAppointmentList:
    def __init__(self, location_code="MHB", app_date=None, doctor_code=None, visit_type=None):
        self.location_code = location_code
        self.app_date = app_date
        self.doctor_code = doctor_code
        self.visit_type = visit_type

    def serialize(self, serializer):
        serializer.start_object('doctorappParam')
        serializer.add_property('LocationCode', self.location_code)
        serializer.add_property('AppDate', self.app_date)
        serializer.add_property('DoctorCode', self.doctor_code)
        serializer.add_property('VisitType', self.visit_type)


class PatientAppStatus:
    def __init__(self, param):
        self.hospital_code = param.get("hospital_code", None)
        self.trans_date = param.get("trans_date", None)
        self.trans_time = param.get("trans_time", None)
        self.android_download = str(param.get("android_download","0"))
        self.ios_download = str(param.get("ios_download","0"))
        self.linked_user_count = str(param.get("linked_user_count","0"))
        self.family_member_count = str(param.get("family_member_count","0"))
        self.primary_user_count = str(param.get("primary_user_count") or "0")
        self.hv_count = str(param.get("hv_count") or "0")
        self.vc_count = str(param.get("vc_count") or "0")
        self.hc_count = str(param.get("hc_count") or "0")
        self.hv_amount = str(param.get("hv_amount") or "0")
        self.vc_amount = str(param.get("vc_amount") or "0")
        self.ip_deposit_amount = str(param.get("ip_deposit_amount") or "0")
        self.ip_deposit_count = str(param.get("ip_deposit_count") or "0")
        self.hc_package_amount = str(param.get("hc_package_amount") or "0")
        self.op_outstanding_amount = str(
            param.get("op_outstanding_amount") or "0")
        self.registered_patient_count = str(
            param.get("registered_patient_count") or "0")
        self.registration_amount = str(param.get("registration_amount") or "0")
        self.home_collection_count = str(
            param.get("home_collection_count") or "0")
        self.home_service_count = str(param.get("home_service_count") or "0")
        self.preferred_hospital_count = str(
            param.get("preferred_hospital_count") or "0")

    def serialize(self, serializer):
        serializer.start_object('PatAppStatsParam')
        serializer.add_property('HospitalCode', self.hospital_code)
        serializer.add_property('TransDate', self.trans_date)
        serializer.add_property('TransTime', self.trans_time)
        serializer.add_property('AndroidDownloads', self.android_download)
        serializer.add_property('IOSDownloads', self.ios_download)
        serializer.add_property('LinkedUserCount', self.linked_user_count)
        serializer.add_property('FamilyMemberCount', self.family_member_count)
        serializer.add_property('PrimaryUserCount', self.primary_user_count)
        serializer.add_property('HVCount', self.hv_count)
        serializer.add_property('VCCount', self.vc_count)
        serializer.add_property('HCCount', self.hc_count)
        serializer.add_property('HVPaymentAmt', self.hv_amount)
        serializer.add_property('VCPaymentAmt', self.vc_amount)
        serializer.add_property('IPDepositTransCount', self.ip_deposit_count)
        serializer.add_property('IPDepositAmt', self.ip_deposit_amount)
        serializer.add_property('HCPkgAmt', self.hc_package_amount)
        serializer.add_property('OPOutstandingPaid',
                                self.op_outstanding_amount)
        serializer.add_property('RegisteredPatientCount',
                                self.registered_patient_count)
        serializer.add_property('UHIDRegistrationAmt',
                                self.registration_amount)
        serializer.add_property('HomeCollectionRqstCount',
                                self.home_collection_count)
        serializer.add_property('HomeServiceRqstCount',
                                self.home_service_count)
        serializer.add_property('PrefHospitalUserCount',
                                self.preferred_hospital_count)

class CheckAppointmentPaymentStatus:

    def __init__(self, param):
        self.appointment_id = param.get("appointment_id", None)
        self.location_code = param.get("location_code", None)
        
    def serialize(self, serializer):
        serializer.start_object('checkAppPaymentStatusParam')
        serializer.add_property('AppointmentId', self.appointment_id)
        serializer.add_property('LocationCode', self.location_code)
        

class PaymentUpdate:
    def __init__(self, param):
        self.uhid = param.get("uhid", None)
        self.transaction_number = param.get("transaction_number", "CORPORATE_INFOSYS")
        self.processing_id = param.get("processing_id", "CORPORATE")
        self.source = param.get("source", "PatientApp")
        self.drawer = param.get("drawer", "NA")
        self.amt = param.get("amt", "0")
        self.location_code = param.get("location_code", None)
        self.app_date = param.get("app_date", None)
        self.package_code = param.get("package_code", "NA")
        self.type = param.get("type", "A")
        self.app_id = param.get("app_id", None)
        self.plan_code = param.get("plan_code", None) or "NA"
        self.is_followup = param.get("is_followup", "N") or "N"
        self.aadhar_number = param.get("aadhar_number", "") or ""
        self.beneficiary_reference_id = param.get("beneficiary_reference_id", "") or ""

    def serialize(self, serializer):
        serializer.start_object('OnlinePaymentParam')
        serializer.add_property('hospno', self.uhid)
        serializer.add_property('tranno', self.transaction_number)
        serializer.add_property('ProcessID', self.processing_id)
        serializer.add_property('Source', self.source)
        serializer.add_property('Drawer', self.drawer)
        serializer.add_property('amt', self.amt)
        serializer.add_property('HospCode', self.location_code)
        serializer.add_property('AppDate', self.app_date)
        serializer.add_property('PkagCode', self.package_code)
        serializer.add_property('Ttype', self.type)
        serializer.add_property('ApptId', self.app_id)
        serializer.add_property('PlanCode', self.plan_code)
        serializer.add_property('IsFollowUp', self.is_followup)
        serializer.add_property('AdhaarId', self.aadhar_number)
        serializer.add_property('CoWinRefId', self.beneficiary_reference_id)

class UHIDPaymentUpdate:
    def __init__(self, param):
        self.location_code = param.get("location_code", None)
        self.temp_id = param.get("temp_id", None)
        self.gateway_id = param.get("gateway_id", "")
        self.transaction_number = param.get("transaction_number", "CORPORATE_INFOSYS")
        self.amt = param.get("amt", "0")
        self.app_date = param.get("app_date", "")
        self.mobile = param.get("mobile", None)
        self.appiontment_identifier = param.get("appiontment_identifier", "")
        self.discount_amt = param.get("discount_amt", "")
        self.discount_reason = param.get("discount_reason", "")
        self.pay_mode = param.get("pay_mode", "")
        
    def serialize(self, serializer):
        serializer.start_object('RegPayementParam')
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('fcrId', self.temp_id)
        serializer.add_property('gatewayId', self.gateway_id)
        serializer.add_property('transactionReferenceId', self.transaction_number)
        serializer.add_property('amount', self.amt)
        serializer.add_property('dateTimeOfTranaction', self.app_date)
        serializer.add_property('mobileno', self.mobile)
        serializer.add_property('appiontmentIdentifier',self.appiontment_identifier)
        serializer.add_property('discountAmount',self.discount_amt)
        serializer.add_property('discountReason',self.discount_reason)
        serializer.add_property('payMode',self.pay_mode)


class OPBillingPaymentUpdate:
    def __init__(self, param):
        self.uhid = param.get("uhid", None)
        self.transaction_number = param.get("transaction_number", "NA")
        self.processing_id = param.get("processing_id", "NA")
        self.source = param.get("source", "PatientApp")
        self.gateway_id = param.get("gateway_id", "")
        self.amt = param.get("amt", "0")
        self.location_code = param.get("location_code", None)
        self.episode_number = param.get("episode_number", "")
        
    def serialize(self, serializer):
        serializer.start_object('OPBillingParam')
        serializer.add_property('hospitalno', self.uhid)
        serializer.add_property('tranno', self.transaction_number)
        serializer.add_property('processingId', self.processing_id)
        serializer.add_property('source', self.source)
        serializer.add_property('gatewayid', self.gateway_id)
        serializer.add_property('amount', str(self.amt))
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('admno', self.episode_number)

class IPDepositPaymentUpdate:
    def __init__(self, param):
        self.uhid = param.get("uhid", None)
        self.transaction_number = param.get("transaction_number", "NA")
        self.auth_code = param.get("auth_code", "9999")
        self.branch = param.get("branch", "PatientApp")
        self.drawer = param.get("drawer", "NA")
        self.amt = param.get("amt", "0")
        self.location_code = param.get("location_code", None)
        
    def serialize(self, serializer):
        serializer.start_object('InsertOnlinePatientDepositParam')
        serializer.add_property('hospitalno', self.uhid)
        serializer.add_property('tranno', self.transaction_number)
        serializer.add_property('authcode', self.auth_code)
        serializer.add_property('branch', self.branch)
        serializer.add_property('drawer', self.drawer)
        serializer.add_property('amount', self.amt)
        serializer.add_property('locationCode', self.location_code)

class CorporateRegistration:
    def __init__(self, temp_id=None, location_code=None, transaction_id="Infosys", amount=0, discount_reason="Infosys"):
        self.temp_id = temp_id
        self.location_code = location_code
        self.transaction_id = transaction_id
        self.amount = amount
        self.discount_reason = discount_reason
        self.paymode = None

    def serialize(self, serializer):
        serializer.start_object('RegPayementParam')
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('fcrId', self.temp_id)
        serializer.add_property('transactionReferenceId', self.transaction_id)
        serializer.add_property('amount', self.amount)
        serializer.add_property('discountReason', self.discount_reason)
        serializer.add_property('payMode', self.paymode)


class LinkUhid:
    def __init__(self, uhid=None, location_code="MHB"):
        self.uhid = uhid
        self.location_code = location_code

    def serialize(self, serializer):
        serializer.start_object('LinkUHIDParam')
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('LocationCode', self.location_code)


class ValidatePatientMobile:
    def __init__(self, uhid=None, location_code="MHB", mobile_no=None):
        self.uhid = uhid
        self.location_code = location_code
        self.mobile_no = mobile_no

    def serialize(self, serializer):
        serializer.start_object('ValidatePatientParam')
        serializer.add_property('mobileno', self.mobile_no)
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('locationCode', self.location_code)


class UhidBasedConsultation:
    def __init__(self, uhid="None", location_code=None, specialty_code=None, doctor_code=None, promo_code="None", order_date=None):
        self.uhid = uhid
        self.location_code = location_code
        self.specialty_code = specialty_code
        self.doctor_code = doctor_code
        self.promo_code = promo_code
        self.order_date = order_date

    def serialize(self, serializer):
        serializer.start_object('consultchargesParam')
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('specialtyCode', self.specialty_code)
        serializer.add_property('doctorCode', self.doctor_code)
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('PromoCode', self.promo_code)
        serializer.add_property('OrderDate', self.order_date)
        
class DriveItemPrice:
    def __init__(self, location_code=None,item_code=None,order_date=None):
        self.location_code = location_code
        self.item_code = item_code
        self.order_date = order_date
        
    def serialize(self, serializer):
        serializer.start_object('OPItemPriceParam')
        serializer.add_property('locationCode', self.location_code)
        serializer.add_property('ItemCode', self.item_code)
        serializer.add_property('OrdDate', self.order_date)
        
