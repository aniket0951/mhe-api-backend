from django.db import models

from apps.users.models import BaseUser
from apps.meta_app.models import MyBaseModel
from apps.master_data.models import Hospital


class AdminMenu(MyBaseModel):
    name = models.CharField(blank=False, null=False,
                            max_length=200, default='Admin menu', unique=True)

    parent_menu = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name


class AdminRole(MyBaseModel):

    name = models.CharField(max_length=200, blank=False,
                            null=False, default='Admin Role', unique=True)

    menus = models.ManyToManyField(AdminMenu, null=True)

    def __str__(self):
        return self.name


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

    hospital = models.ForeignKey(
        Hospital, null=True, on_delete=models.PROTECT, related_name='hospital_name')

    role = models.ForeignKey(AdminRole, on_delete=models.PROTECT, null=True)

    isPcc = models.BooleanField(default=False)

    menus = models.ManyToManyField(AdminMenu, null=True)

    secret_key = models.CharField(max_length=200,
                                  blank=True,
                                  null=True,
                                  verbose_name='secret_key')

    secret_token = models.CharField(max_length=200,
                                    blank=True,
                                    null=True,
                                    verbose_name='secret_token')

    @property
    def representation(self):
        return 'Email: {} Name: {}'.format(self.email, self.name)

    class Meta:
        verbose_name = "Manipal Admin"
        verbose_name_plural = "Manipal Admin"

    def __str__(self):
        return self.representation
