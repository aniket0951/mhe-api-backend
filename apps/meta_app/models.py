import uuid
from django.contrib.auth.models import Group
from django.db import models

class MyBaseModel(models.Model):
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class AutoIncrementBaseModel(models.Model):
    registration_no = models.AutoField(primary_key=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserTypes(Group):
    slug = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    description = models.CharField(max_length=200,
                                   null=False,
                                   blank=False,
                                   )

    @property
    def representation(self):
        return 'Name: {} Description: {}'.format(self.name, self.description)

    class Meta:
        verbose_name = "User Type"
        verbose_name_plural = "Users Types"

    def __str__(self):
        return self.representation

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().strip().replace(" ", "_")
        super(UserTypes, self).save(*args, **kwargs)
