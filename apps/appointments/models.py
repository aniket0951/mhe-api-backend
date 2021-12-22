import logging
import os
from datetime import datetime

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.doctors.models import Doctor
from apps.health_packages.models import HealthPackage
from apps.master_data.models import Department, Hospital
from apps.meta_app.models import MyBaseModel
from apps.patients.models import FamilyMember, Patient
from utils.custom_storage import FileStorage
from utils.validators import validate_file_authenticity, validate_file_size
from django_clamd.validators import validate_file_infection

logger = logging.getLogger('django')

def generate_personal_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "appointment/{0}/documents/{1}".format(self.id, obj_name)


def generate_prescription_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "appointment/{0}/prescriptions/{1}".format(self.id, obj_name)


class CancellationReason(models.Model):

    reason = models.TextField(blank=False,
                              null=False,
                              max_length=100)


class Appointment(models.Model):

    CONFIRMED = 1
    CANCELLED = 2
    WAITING = 3
    COMPLETED = 4
    RESCHEDULED = 5
    REBOOKED = 6
    STATUS_CODES = (
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
        (WAITING, 'Waiting'),
        (COMPLETED, 'Completed'),
        (RESCHEDULED, 'Rescheduled'),
        (REBOOKED, 'Rebooked'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    appointment_date = models.DateField()
    appointment_slot = models.TimeField()
    slot_duration = models.FloatField(default=10,null=False)
    appointment_identifier = models.CharField(max_length=20,
                                              blank=True,
                                              null=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CODES)
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name='patient_appointment')

    family_member = models.ForeignKey(FamilyMember, on_delete=models.PROTECT,
                                      related_name='family_appointment',
                                      blank=True, null=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT,
                               related_name='doctor_appointment')

    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name='hospital_appointment')

    department = models.ForeignKey(Department, on_delete=models.PROTECT,
                                   related_name='hospital_department',
                                   blank=True, null=True)

    reason = models.ForeignKey(CancellationReason, on_delete=models.PROTECT,
                               related_name='cancellation_reason_appointment',
                               null=True, blank=True)
    other_reason = models.TextField(blank=True,
                                    null=True,
                                    max_length=500)

    payment_status = models.CharField(max_length=10,
                                      blank=True,
                                      null=True)
    uhid = models.CharField(max_length=20,
                            blank=True,
                            null=True)
    consultation_amount = models.FloatField(default=0,
                                            null=True)
    refundable_amount = models.FloatField(default=0,
                                          null=True)
    booked_via_app = models.BooleanField(default=True)

    appointment_mode = models.CharField(max_length=10,
                                        default="HV")
    
    appointment_service = models.CharField(max_length=20,default="consultation")

    enable_join_button = models.BooleanField(default=False)

    vc_appointment_status = models.IntegerField(default="1")

    patient_ready = models.BooleanField(default=False)

    episode_number = models.CharField(max_length=30,
                                      blank=True,
                                      null=True)
    
    episode_date_time = models.DateTimeField(auto_now=True)

    corporate_appointment = models.BooleanField(default=False)

    is_follow_up = models.BooleanField(default=False)

    plan_code = models.CharField(max_length=30,blank=True,null=True)

    beneficiary_reference_id = models.CharField(max_length=30,null=True,blank=True)

    root_appointment_id = models.CharField(max_length=50,null=True,blank=True)

    @property
    def is_cancellable(self):
        if self.appointment_date and ((self.appointment_date >= datetime.now().date()) and (self.status == 1)):
            
            registration_amount = 0
            if self.payment_appointment.exists():
                payment_instance = self.payment_appointment.first()
                if payment_instance.payment_for_uhid_creation:
                    from apps.payments.utils import PaymentUtils
                    registration_amount = PaymentUtils.add_items_tariff_price(0,self.hospital.code)
            
            if self.appointment_date > datetime.now().date():
                if self.payment_status == "success":
                    self.refundable_amount = self.consultation_amount - registration_amount
                    self.save()
                return True

            if self.appointment_date == datetime.now().date() and self.appointment_slot > datetime.now().time():
                # if not self.payment_status:
                #     return True

                date_time_slot = datetime.combine(datetime.now(), self.appointment_slot)
                logger.info("date_time_slot --> %s"%(str(date_time_slot)))
                date_time_now = datetime.combine(datetime.now(), datetime.now().time())
                logger.info("date_time_now --> %s"%(str(date_time_now)))
                time_delta = (date_time_slot - date_time_now).total_seconds()/3600
                logger.info("time_delta --> %s"%(str(time_delta)))

                if time_delta > 2:
                    self.refundable_amount = self.consultation_amount - registration_amount

                    if time_delta <= 4:
                        self.refundable_amount = self.consultation_amount - registration_amount - 100.0

                    self.save()
                    return True
        self.save()
        return False
    
    @property
    def is_admin_cancellable(self):
        if self.appointment_date and ((self.appointment_date >= datetime.now().date()) and (self.status == 1)):
            
            registration_amount = 0
            if self.payment_appointment.exists():
                payment_instance = self.payment_appointment.first()
                if payment_instance.payment_for_uhid_creation:
                    from apps.payments.utils import PaymentUtils
                    registration_amount = PaymentUtils.add_items_tariff_price(0,self.hospital.code)
            
            if self.appointment_date > datetime.now().date():
                if self.payment_status == "success":
                    self.refundable_amount = self.consultation_amount - registration_amount
                    self.save()
                    return True

            if self.appointment_date == datetime.now().date() and self.appointment_slot > datetime.now().time():
                if not self.payment_status:
                    return True

                date_time_slot = datetime.combine(datetime.now(), self.appointment_slot)
                date_time_now = datetime.combine(datetime.now(), datetime.now().time())
                time_delta = (date_time_slot - date_time_now).total_seconds()/3600

                if time_delta > 0.5:
                    self.refundable_amount = self.consultation_amount - registration_amount

                    if time_delta <= 4:
                        self.refundable_amount = self.consultation_amount - registration_amount - 100.0

                    self.save()
                    return True
        self.save()
        return False

    @property
    def is_payment_option_enabled(self):
        if self.appointment_date and ((self.appointment_date < datetime.now().date()) or ((self.appointment_date == datetime.now().date()) and (self.appointment_slot < datetime.now().time()))):
            return False
        return True


class HealthPackageAppointment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    appointment_date = models.DateTimeField(blank=True, null=True)

    appointment_identifier = models.CharField(max_length=20,
                                              blank=True,
                                              null=True)

    appointment_status = models.CharField(max_length=10,
                                          default="Not Booked")

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT,
                                related_name='patient_health_package_appointment')

    family_member = models.ForeignKey(FamilyMember, on_delete=models.PROTECT,
                                      related_name='family_health_package_appointment', blank=True,
                                      null=True)

    health_package = models.ManyToManyField(HealthPackage,
                                            blank=True,
                                            null=True
                                            )
    health_package_original = JSONField(null=True, blank=True)

    payment = models.ForeignKey('payments.Payment', on_delete=models.PROTECT,
                                related_name='payment_health_package_appointment',
                                blank=True, null=True)

    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT,
                                 related_name='hospital_health_appointment')

    reason = models.ForeignKey(CancellationReason, on_delete=models.PROTECT,
                               related_name='cancellation_reason_health_appointment',
                               null=True, blank=True)
    other_reason = models.TextField(blank=True,
                                    null=True,
                                    max_length=500)

    booked_via_app = models.BooleanField(default=True)

    @property
    def is_cancellable(self):
        if self.appointment_date and ((self.appointment_date > datetime.now()) and (self.appointment_status != "Cancelled")):
            return True
        return False


class AppointmentDocuments(MyBaseModel):
    DOCUMENT_TYPE_CHOICES = (
        ('Prescription', 'Prescription'),
        ('Lab', 'Lab'),
        ('Radiology', 'Radiology'),


    )

    name = models.CharField(max_length=500,
                            blank=False,
                            null=False)

    document = models.FileField(upload_to=generate_personal_file_path,
                                storage=FileStorage(),
                                validators=[
                                        FileExtensionValidator(settings.VALID_FILE_EXTENSIONS), 
                                        validate_file_size,
                                        validate_file_authenticity,
                                        validate_file_infection
                                ],
                                blank=False,
                                null=False)

    document_type = models.CharField(choices=DOCUMENT_TYPE_CHOICES,
                                     default='Prescription',
                                     max_length=15
                                     )

    appointment_info = models.ForeignKey(Appointment,
                                         on_delete=models.PROTECT,
                                         null=False,
                                         blank=False,
                                         related_name='appointment_documents')

    @property
    def representation(self):
        return 'Appointment: {}, Document: {}'.format(self.appointment_info.appointment_identifier, self.name)

    class Meta:
        verbose_name = "Appointment Document"
        verbose_name_plural = "Appointment Documents"

    def __str__(self):
        return self.representation


class AppointmentVital(MyBaseModel):

    blood_pressure = models.CharField(max_length=15,
                                      blank=True,
                                      null=True)

    body_temperature = models.CharField(max_length=15,
                                        blank=True,
                                        null=True)

    height = models.CharField(max_length=15,
                              blank=True,
                              null=True)

    weight = models.CharField(max_length=15,
                              blank=True,
                              null=True)

    appointment_info = models.ForeignKey(Appointment,
                                         on_delete=models.PROTECT,
                                         null=False,
                                         blank=False,
                                         related_name='appointment_vitals')

    class Meta:
        verbose_name = "Appointment Document"
        verbose_name_plural = "Appointment Documents"


class PrescriptionDocuments(MyBaseModel):

    name = models.CharField(max_length=500,
                            blank=False,
                            null=False)

    prescription = models.FileField(upload_to=generate_prescription_file_path,
                                    storage=FileStorage(),
                                    validators=[
                                        FileExtensionValidator(settings.VALID_FILE_EXTENSIONS), 
                                        validate_file_size,
                                        validate_file_authenticity,
                                        validate_file_infection
                                    ],
                                    blank=False,
                                    null=False)

    appointment_info = models.ForeignKey(Appointment,
                                         on_delete=models.PROTECT,
                                         null=False,
                                         blank=False,
                                         related_name='appointment_presciptions',
                                         )
    appointment_identifier = models.CharField(max_length=50,
                                              blank=True,
                                              null=True)

    episode_number = models.CharField(max_length=50,
                                      blank=True,
                                      null=True)

    episode_date_time = models.DateTimeField(auto_now=True)

    file_type = models.CharField(max_length=50,
                                 default="Prescription")

    hospital_code = models.CharField(max_length=10,
                                     blank=True,
                                     null=True)

    department_code = models.CharField(max_length=10,
                                       blank=True,
                                       null=True)

    class Meta:
        verbose_name = "Appointment Prescription"
        verbose_name_plural = "Appointment Prescriptions"


class Feedbacks(MyBaseModel):

    feedback = models.TextField(blank=False,
                                null=False,
                                max_length=500)

    rating = models.IntegerField(default="1")

    user_id = models.OneToOneField(
        Patient, related_name='feedback_user', on_delete=models.PROTECT)

    platform = models.CharField(max_length=20, choices=(
        ('iOS', 'iOS'), ('Android', 'Android'),))

    version = models.CharField(max_length=30, blank=True, null=True)


class AppointmentPrescription(MyBaseModel):

    appointment_info = models.ForeignKey(Appointment, on_delete=models.PROTECT,
                                         related_name='appointment_prescription',
                                         blank=True,
                                         null=True)

    prescription_documents = models.ManyToManyField(PrescriptionDocuments,
                                                    blank=True,
                                                    null=True
                                                    )

    
class PrimeBenefits(MyBaseModel):

    sequence = models.IntegerField()
    
    description = models.CharField(
                        max_length=500,
                        null=True,
                        blank=True
                    )

    hospital_info = models.ManyToManyField(
                                        Hospital,
                                        blank=True,
                                        null=True,
                                        related_name='prime_benefits_hospital'
                                    )
    