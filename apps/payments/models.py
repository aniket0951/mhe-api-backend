from django.contrib.postgres.fields import JSONField
from django.db import models

from apps.appointments.models import Appointment
from apps.health_packages.models import HealthPackage
from apps.master_data.models import HomeCareService, Hospital
from apps.meta_app.models import MyBaseModel
from apps.patients.models import FamilyMember, Patient


class Payment(MyBaseModel):

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

    bank_ref_num = models.CharField(max_length=50,
                                    null=True,
                                    blank=True,
                                    )
                                    

    settled_at = models.DateField(null=True, blank=True)

    uhid_number = models.CharField(max_length=20,
                                   blank=True,
                                   null=True)

    location = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 blank=True,
                                 null=True)

    appointment = models.ForeignKey(Appointment,
                                    on_delete=models.PROTECT,
                                    blank=True,
                                    null=True)

    health_package = models.ManyToManyField(HealthPackage,
                                            blank=True,
                                            null=True
                                            )
    payment_method = models.CharField(max_length=10,
                                      blank = True,
                                      null = True)

    patient = models.ForeignKey(Patient,
                                on_delete=models.PROTECT,
                                blank=False,
                                null=False, related_name="payment_patient")

    payment_done_for_patient = models.ForeignKey(Patient,
                                     on_delete=models.PROTECT,
                                     blank=True,
                                     null=True)
    payment_done_for_family_member = models.ForeignKey(FamilyMember,
                                           on_delete=models.SET_NULL,
                                           blank=True,
                                           null=True)
    payment_for_uhid_creation = models.BooleanField(default=False)
    payment_for_ip_deposit = models.BooleanField(default=False)
    payment_for_op_billing = models.BooleanField(default=False)
    payment_for_health_package = models.BooleanField(default=False)
    episode_number = models.CharField(max_length=20,
                                      blank=True,
                                      null=True)

    raw_info_from_salucro_response = JSONField(blank=True,
                                               null=True
                                               )
