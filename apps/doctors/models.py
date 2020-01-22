import uuid

from django.db import models

from apps.master_data.models import Hospital, Specialisation
# Create your models here.
from apps.users.models import BaseUser


class Doctor(BaseUser):

    code = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    linked_hospitals = models.ManyToManyField(Hospital,
                                              blank=False)

    specialisations = models.ManyToManyField(Specialisation,
                                             blank=False)

    designation = models.CharField(max_length=150,
                                   null=False,
                                   blank=False,
                                   )

    awards_and_achievements = models.TextField(blank=True,
                                               null=True)
    experience = models.IntegerField(blank=True, null=True)

    start_date = models.DateField()

    end_date = models.DateField()

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"
        permissions = ()

    def __str__(self):
        return self.representation
