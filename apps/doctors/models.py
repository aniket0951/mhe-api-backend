import uuid

from django.db import models

from apps.master_data.models import (Department, Hospital, HospitalDepartment,
                                     Specialisation)
from apps.users.models import BaseUser


class Doctor(BaseUser):

    name = models.CharField(max_length=200,
                            blank=False,
                            null=False,
                            verbose_name='First Name')

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

    hv_consultation_charges = models.IntegerField(default=0,
                                                  null=True)

    vc_consultation_charges = models.IntegerField(default=0,
                                                  null=True)

    pr_consultation_charges = models.IntegerField(default=0,
                                                  null=True)

    qualification = models.CharField(max_length=800,
                                     null=True,
                                     blank=True,
                                     )

    designation = models.CharField(max_length=500,
                                   null=True,
                                   blank=True,
                                   )

    field_expertise = models.TextField(
        null=True,
        blank=True,
    )

    languages_spoken = models.CharField(max_length=500,
                                        null=True,
                                        blank=True,
                                        )

    awards_achievements = models.TextField(
        null=True,
        blank=True,
    )

    fellowship_membership = models.TextField(
        null=True,
        blank=True,
    )

    photo = models.URLField(max_length=300,
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

    is_online_appointment_enable = models.BooleanField(default=True)

    @property
    def representation(self):
        return 'Name: {} Code: {} Hospital: {}'.format(self.name, self.code, self.hospital.description)

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"
        permissions = ()
        unique_together = [['code', 'hospital'], ]

    def __str__(self):
        return self.representation
