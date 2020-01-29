from django.db import models

import uuid

# Create your models here.
from apps.users.models import BaseUser


class Relationship(BaseUser):

    relation = models.CharField(max_length = 200)

    class Meta:
        verbose_name = "Relationship"
        verbose_name_plural = "Relationships"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Relationship, self).save(*args, **kwargs)


class Patient(BaseUser):
    unique_identifier = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)

    associated_users = models.ManyToManyField('self')

    # relation_id = models.CharField(max_length = 200)
    # reverse_relation_id = models.CharField(max_length = 200)
    relation_id = models.ForeignKey(
        Relationship,
        related_name = 'direct_relation',
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    reverse_relation_id = models.ForeignKey(
        Relationship,
        related_name = 'reverse_relation',
        on_delete=models.PROTECT,
        null=False,
        blank=False)


    @property
    def representation(self):
        return 'Unique Manipal Identifier: {} Name: {}'.format(self.unique_identifier, self.first_name)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        permissions = ()

    def __str__(self):
        return self.representation
