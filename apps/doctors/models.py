import uuid

from django.db import models

from apps.master_data.models import Department, Hospital, Specialisation, HospitalDepartment
from apps.users.models import BaseUser


class Doctor(BaseUser):

    code = models.CharField(max_length=300,
                            null=False,
                            blank=False,
                            )
    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 blank=False,
                                 null=False)

    hospital_departments = models.ManyToManyField(HospitalDepartment,
                                                  blank=True,
                                                  related_name='doctor')

    specialisations = models.ManyToManyField(Specialisation,
                                             blank=True,
                                             related_name='doctor')

    consultation_charges = models.IntegerField(default=0,
                                               null=True)

    qualification = models.CharField(max_length=300,
                                     null=True,
                                     blank=True,
                                     )

    educational_degrees = models.CharField(max_length=300,
                                           null=True,
                                           blank=True,
                                           )
    notes = models.TextField(blank=True,
                             null=True)

    experience = models.IntegerField(blank=True, null=True)

    start_date = models.DateField(blank=False,
                                  null=False,)

    end_date = models.DateField(blank=True,
                                null=True)

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"
        permissions = ()
        unique_together = [['code', 'hospital'], ]

    def __str__(self):
        return self.code
