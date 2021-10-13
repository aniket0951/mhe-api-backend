from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from apps.master_data.models import Hospital
from apps.meta_app.models import MyBaseModel
from apps.users.models import BaseUser

class Phlebo(BaseUser):
    
    first_name = models.CharField(
                            max_length=200, 
                            blank=False, 
                            null=False
                        )
    
    last_name = models.CharField(
                            max_length=200, 
                            blank=False, 
                            null=False
                        )
    
    hospital = models.ForeignKey(
                            Hospital, 
                            on_delete=models.PROTECT,
                            blank=False,
                            null=False,
                            related_name='phlebo_hospital'
                        )
    
    otp_expiration_time = models.DateTimeField(
                                        blank=True,
                                        null=True,
                                        verbose_name='OTP Expiration Date Time')

    mobile_verified = models.BooleanField(default=False,
                                          verbose_name='Mobile Verified')

    
    start_date = models.DateField()
    
    end_date = models.DateField()
    
class PhleboRegion(MyBaseModel):
    
    phlebo = models.ForeignKey(
                        Phlebo, 
                        on_delete=models.PROTECT,
                        related_name='phlebo'      
                    )
    
    pin = models.CharField(max_length=10)
    


