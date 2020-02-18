from django.db import models

from apps.users.models import BaseUser


class ManipalAdmin(BaseUser):

    class Meta:
        verbose_name = "Manipal Admin"
        verbose_name_plural = "Manipal Admin"

    def __str__(self):
        return self.first_name

