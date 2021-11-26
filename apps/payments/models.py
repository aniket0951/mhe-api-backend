import os
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.health_packages.models import HealthPackage
from apps.master_data.models import HomeCareService, Hospital
from apps.meta_app.models import MyBaseModel
from apps.patients.models import FamilyMember, Patient
from fernet_fields import EncryptedTextField
from utils.custom_storage import FileStorage
from utils.validators import validate_file_authenticity, validate_file_size
from django_clamd.validators import validate_file_infection


def generate_receipt_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "payment/{0}/receipts/{1}".format(self.id, obj_name)


class Payment(MyBaseModel):

    razor_invoice_id = models.CharField(max_length=50, null=True, blank=True, default="0")

    razor_order_id = models.CharField(max_length=50, null=False, blank=False, default="0")

    razor_payment_id = models.CharField(max_length=50, null=True, blank=True)

    processing_id = models.CharField(max_length=50,
                                     null=False,
                                     blank=False,
                                     )

    transaction_id = models.CharField(max_length=50,
                                      null=True,
                                      blank=True,
                                      )

    status = models.CharField(max_length=10,
                              default="Initiated")

    amount = models.FloatField(default=0,
                               null=True)

    receipt_number = models.CharField(max_length=50,
                                      null=True,
                                      blank=True,
                                      )

    settled_at = models.DateTimeField(blank=True, null=True)

    uhid_number = models.CharField(max_length=20,
                                   blank=True,
                                   null=True)

    location = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 blank=True,
                                 null=True)

    appointment = models.ForeignKey(Appointment,
                                    related_name="payment_appointment",
                                    on_delete=models.PROTECT,
                                    blank=True,
                                    null=True)

    health_package_appointment = models.ForeignKey(HealthPackageAppointment,
                                                   related_name="payment_health_package_appointment",
                                                   on_delete=models.PROTECT,
                                                   blank=True, null=True)

    payment_method = models.CharField(max_length=70,
                                      blank=True,
                                      null=True)

    patient = models.ForeignKey(Patient,
                                on_delete=models.PROTECT,
                                blank=False,
                                null=False, related_name="payment_patient")

    payment_done_for_patient = models.ForeignKey(Patient,
                                                 on_delete=models.PROTECT,
                                                 blank=True,
                                                 null=True)

    payment_done_for_family_member = models.ForeignKey(FamilyMember,
                                                       on_delete=models.PROTECT,
                                                       blank=True,
                                                       null=True)

    payment_for_uhid_creation = models.BooleanField(default=False)

    payment_for_ip_deposit = models.BooleanField(default=False)

    payment_for_op_billing = models.BooleanField(default=False)

    payment_for_health_package = models.BooleanField(default=False)

    payment_for_drive = models.BooleanField(default=False)

    episode_number = models.CharField(max_length=20,
                                      blank=True,
                                      null=True)

    bill_row_id = models.CharField(max_length=20,
                                      blank=True,
                                      null=True)

    raw_info_from_salucro_response = JSONField(blank=True,
                                               null=True
                                               )
    raw_info_from_manipal_response = JSONField(blank=True,
                                               null=True
                                               )


class PaymentRefund(MyBaseModel):

    
    refund_id = models.CharField(max_length=50, null=False, blank=False, default="0")

    razor_payment_id = models.CharField(max_length=50, null=False, blank=False, default="0")


    payment = models.ForeignKey(Payment,
                                on_delete=models.PROTECT,
                                blank=True,
                                null=True, related_name="payment_refund")

    uhid_number = models.CharField(max_length=20,
                                   blank=True,
                                   null=True)

    processing_id = models.CharField(max_length=50,
                                     null=False,
                                     blank=False,
                                     )
    transaction_id = models.CharField(max_length=50,
                                      null=True,
                                      blank=True,
                                      )
    status = models.CharField(max_length=10,
                              default="Pending")

    amount = models.FloatField(default=0,
                               null=True)

    receipt_number = models.CharField(max_length=50,
                                      null=True,
                                      blank=True,
                                      )
    request_id = models.CharField(max_length=50,
                                  null=True,
                                  blank=True,
                                  )

class UnprocessedTransactions(MyBaseModel):

    UNPROCESSED = "unprocessed"
    PROCESSED = "processed"
    REFUNDED = "refunded"

    STATUS_CHOICES = (
        (UNPROCESSED,UNPROCESSED),
        (PROCESSED,PROCESSED),
        (REFUNDED,REFUNDED),
    )

    payment = models.ForeignKey(Payment,
                                 on_delete=models.PROTECT,
                                 related_name="unprocessed_transactions_payment",
                                 blank=False,
                                 null=False)

    appointment = models.ForeignKey(Appointment,
                                    related_name="unprocessed_transactions_appointment",
                                    on_delete=models.PROTECT,
                                    blank=True,
                                    null=True)
    
    health_package_appointment = models.ForeignKey(HealthPackageAppointment,
                                 on_delete=models.PROTECT,
                                 blank=True,
                                 null=True)
    
    patient = models.ForeignKey(Patient,
                                on_delete=models.PROTECT,
                                blank=False,
                                null=False)
    
    family_member = models.ForeignKey(FamilyMember,
                                on_delete=models.PROTECT,
                                blank=True,
                                null=True)

    status = models.CharField(
                        choices=STATUS_CHOICES,
                        max_length=100,
                        default=UNPROCESSED,
                        blank=False,
                        null=False)

    retries = models.IntegerField(default=0)


class PaymentHospitalKey(MyBaseModel):

    hospital = models.ForeignKey(Hospital,
                                 related_name="payment_hospital_key_hospital",
                                 on_delete=models.PROTECT,
                                 blank=True, null=True)

    mid = EncryptedTextField(blank=True, null=True)

    secret_key = EncryptedTextField(blank=True, null=True)
    secret_secret = EncryptedTextField(blank=True, null=True)


class PaymentReceipts(MyBaseModel):

    uhid = models.CharField(max_length=50,
                            null=True,
                            blank=True,
                            )

    name = models.CharField(max_length=500,
                            blank=False,
                            null=False)

    receipt = models.FileField(upload_to=generate_receipt_file_path,
                               storage=FileStorage(),
                               validators=[
                                   FileExtensionValidator(settings.VALID_FILE_EXTENSIONS), 
                                   validate_file_size,
                                   validate_file_authenticity,
                                   validate_file_infection
                                ],
                               blank=False,
                               null=False)

    patient_info = models.ForeignKey(Patient,
                                     on_delete=models.PROTECT,
                                     blank=True,
                                     null=True,
                                     related_name='patient_receipt',)

    payment_info = models.ForeignKey(Payment,
                                     on_delete=models.PROTECT,
                                     null=True,
                                     blank=True,
                                     related_name='payment_receipt',
                                     )

    receipt_date = models.DateTimeField(blank=True, null=True)
