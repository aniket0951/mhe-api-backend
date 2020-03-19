from django.db import models
from django.contrib.postgres.fields import JSONField
from apps.appointments.models import Appointment
from apps.health_packages.models import HealthPackage
from apps.master_data.models import HomeCareService
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
                              default= "INITIAL")
    amount = models.FloatField(default=0,
                                 null=True)

    bank_ref_num = models.CharField(max_length=50,
                                      null=True,
                                      blank=True,
                                      )

    settled_at = models.DateField(null = True, blank = True)

    uhid_number = models.CharField(max_length=20,
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
    patient = models.ForeignKey(Patient,
                                     on_delete=models.PROTECT,
                                     blank=False,
                                     null=False, related_name = "payment_patient")
                                            
    uhid_patient = models.ForeignKey(Patient,
                                     on_delete=models.PROTECT,
                                     blank=True,
                                     null=True)
    uhid_family_member = models.ForeignKey(FamilyMember,
                                           on_delete=models.PROTECT,
                                           blank=True,
                                           null=True)
    raw_info_from_salucro_response = JSONField(blank=True,
                                               null=True
                                               )
