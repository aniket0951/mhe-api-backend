import uuid

from django.db import models

from apps.master_data.models import (Department, Hospital, HospitalDepartment,
                                     Specialisation)
from apps.meta_app.models import MyBaseModel
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
                                                  related_name='doctor_hospital_department')

    specialisations = models.ManyToManyField(Specialisation,
                                             blank=True,
                                             related_name='doctor_specialisation')
    
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

    talks_publications = models.TextField(
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


class DoctorCharges(MyBaseModel):

    doctor_info = models.ForeignKey(Doctor,
                                    on_delete=models.PROTECT,
                                    blank=False,
                                    null=False)

    department_info = models.ForeignKey(Department,
                                        blank=True,
                                        on_delete=models.PROTECT,
                                        related_name='doctor_hospital_department_charges')

    hv_consultation_charges = models.IntegerField(default=0,
                                                  null=True)

    vc_consultation_charges = models.IntegerField(default=0,
                                                  null=True)

    pr_consultation_charges = models.IntegerField(default=0,
                                                  null=True)

    plan_code = models.CharField(
                            max_length=50,
                            blank=True,
                            null=True
                        )

    class Meta:
        verbose_name = "Consultation Charges"
        verbose_name_plural = "Consultation charges"


class DoctorsWeeklySchedule(MyBaseModel):

    SERVICES = (
        ('HV','HV'),
        ('VC','VC'),
        ('HVVC','HVVC'),
        ('PR','PR'),
    )

    WEEKDAYS_TYPE = (
        ("Monday", 'Monday'),
        ("Tuesday", 'Tuesday'),
        ("Wednesday", 'Wednesday'),
        ("Thursday", 'Thursday'),
        ("Friday", 'Friday'),
        ("Saturday", 'Saturday'),
        ("Sunday", 'Sunday')
    )

    doctor      = models.ForeignKey(Doctor,
                                on_delete=models.PROTECT,
                                blank=False,
                                null=False
                            )

    department  = models.ForeignKey(Department,
                                blank=True,
                                on_delete=models.PROTECT,
                                related_name='doctor_department_weekly_schedule'
                            )

    hospital    = models.ForeignKey(
                                Hospital,
                                on_delete=models.PROTECT,
                                related_name='doctor_hospital_weekly_schedule'
                            )

    day         = models.CharField(
                            choices=WEEKDAYS_TYPE,
                            max_length=30,
                            null=True,
                            blank=True,
                        )

    service     = models.CharField(
                            choices=SERVICES,
                            blank=True,
                            null=True,
                            max_length=6
                        )

    from_time   = models.TimeField(
                            null=True,
                            blank=True
                        )

    to_time     = models.TimeField(
                            null=True,
                            blank=True
                        )
    
    class Meta:
        verbose_name = "Weekly Schedule"
        verbose_name_plural = "Weekly Schedules"