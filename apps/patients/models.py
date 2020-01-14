from django.db import models

import uuid

# Create your models here.
from apps.users.models import BaseUser

class Patient(BaseUser):
    unique_identifier = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)

    associated_users = models.ManyToManyField('self')

    @property
    def representation(self):
        return 'Unique Manipal Identifier: {} Name: {}'.format(self.unique_identifier, self.first_name)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        permissions = ()

    def __str__(self):
        return self.representation
