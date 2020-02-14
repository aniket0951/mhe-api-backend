from django.db import models

from apps.users.models import BaseUser


class ManipalAdmin(BaseUser):
    role = models.IntegerField(blank=False,
                            null=False,
                            default= 1,
                            verbose_name='Role')

    class Meta:
        verbose_name = "Manipal Admin"
        verbose_name_plural = "Manipal Admin"

    def __str__(self):
        return self.first_name

