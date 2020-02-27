from django.db import models

from apps.users.models import BaseUser


class ManipalAdmin(BaseUser):

    email = models.EmailField(blank=False,
                              null=False,
                              unique=True)

    name = models.CharField(max_length=200,
                            blank=False,
                            null=False,
                            verbose_name='Full Name')

    email_verified = models.BooleanField(default=False,
                                         verbose_name='Email Verified')

    @property
    def representation(self):
        return 'Email: {} Name: {}'.format(self.email, self.name)

    class Meta:
        verbose_name = "Manipal Admin"
        verbose_name_plural = "Manipal Admin"

    def __str__(self):
        return self.representation
