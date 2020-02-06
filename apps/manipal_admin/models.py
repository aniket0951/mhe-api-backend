from django.db import models

from apps.users.models import User


class ManipalAdmin(User):

    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    )

    name = models.CharField(max_length=50,
                                  blank=False,
                                  null=False)
    
    email=models.EmailField(max_length=70, blank=False, unique=True)
    
    email_verified = models.BooleanField(
        default=False,
        verbose_name='Email Verified')

    class Meta:
        verbose_name = "Manipal Admin"
        verbose_name_plural = "Manipal Admin"

    def __str__(self):
        return self.representation

