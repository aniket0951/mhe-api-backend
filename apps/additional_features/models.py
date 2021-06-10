from apps.meta_app.models import MyBaseModel
from django.db import models
    
class StaticInstructions(MyBaseModel):
    instruction_type = models.CharField(
                                    max_length=50,
                                    blank=False,
                                    null=False
                                )
    
    instruction = models.TextField()
    
    sequence = models.IntegerField()
    