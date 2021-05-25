from apps.users.models import BaseUser
import os
import uuid

from django.conf import settings
from django.core.validators import (FileExtensionValidator, MaxValueValidator,
                                    MinValueValidator)
from django.db import models

from apps.meta_app.models import MyBaseModel
from utils.custom_storage import LocalFileStorage, MediaStorage
from utils.validators import validate_file_authenticity, validate_file_size
from django_clamd.validators import validate_file_infection


def generate_banner_picture_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(uuid.uuid4()) + str(obj_file_extension)
    return "static/dashboard/banners/{0}".format(obj_name)

def generate_faq_picture_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(uuid.uuid4()) + str(obj_file_extension)
    return "static/faq/banners/{0}".format(obj_name)

def generate_flyer_picture_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(uuid.uuid4()) + str(obj_file_extension)
    return "static/flyers/{0}".format(obj_name)

class DashboardBanner(MyBaseModel):

    BANNER_TYPE_CHOICES = (
        ('HomeCollection', 'HomeCollection'),
    )

    image = models.ImageField(
                        upload_to=generate_banner_picture_path,
                        storage=MediaStorage(),
                        validators=[
                            FileExtensionValidator(settings.VALID_IMAGE_FILE_EXTENSIONS), 
                            validate_file_size,
                            validate_file_authenticity,
                            validate_file_infection
                        ],
                        blank=False,
                        null=False,
                        verbose_name='Display Picture'
                    )

    banner_type = models.CharField(choices=BANNER_TYPE_CHOICES,
                                   blank=False,
                                   null=False,
                                   default='HomeCollection',
                                   max_length=14,
                                   verbose_name='Banner Type')

    @property
    def representation(self):
        return 'Banner Type: {}'\
            .format(self.banner_type)

    class Meta:
        verbose_name = "Dashboard Banner"
        verbose_name_plural = "Dashboard Banners"

    def __str__(self):
        return self.representation


class FAQData(MyBaseModel):

    BANNER      = 'banner'
    DESCRIPTION = 'description'
    QNA         = 'qna'
    VIDEO       = 'video'
    
    TYPE_CHOICES = (
            (BANNER,        'Banner'),
            (DESCRIPTION,   'Description'),
            (QNA,           'QnA'),
            (VIDEO,         'Video')
        )

    type        = models.CharField(
                            choices=TYPE_CHOICES,
                            default='qna',
                            max_length=15
                        )

    code        = models.SlugField(
                            unique=True,
                            blank=False,
                            null=False
                        )

    question    = models.TextField(
                            blank=True,
                            null=True
                        )

    data        = models.TextField(
                            blank=True,
                            null=True
                        )

    data        = models.TextField(
                            blank=True,
                            null=True
                        )
    
    image       = models.ImageField(
                            upload_to=generate_faq_picture_path,
                            storage=MediaStorage(),
                            validators=[
                                FileExtensionValidator(settings.VALID_IMAGE_FILE_EXTENSIONS), 
                                validate_file_size,
                                validate_file_authenticity,
                                validate_file_infection
                            ],
                            blank=True,
                            null=True,
                            verbose_name='FAQ Picture'
                        )

class FlyerScheduler(MyBaseModel):

    FLYER_SCHEDULER_CHOICES = (
                        (1,'Once-a-Day'),
                        (0,'EveryTime')
                    )

    flyer_name = models.CharField(
                            max_length=150,
                            blank=False,
                            null=False,
                            verbose_name='flyers_name'    
                        )

    start_date_time = models.DateTimeField(
                                    blank=False,
                                    null=False
                                )

    end_date_time = models.DateTimeField(
                                    blank=False,
                                    null=False
                                )

    frequency = models.IntegerField(
                            choices=FLYER_SCHEDULER_CHOICES,
                            blank=False,
                            null=False,
                            default=0
                        )

    is_active = models.BooleanField(
                            default=True
                        )

    created_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            related_name='created_by_base_user',
                            blank=True,
                            null=True
                        )

    updated_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            related_name='updated_by_base_user',
                            blank=True,
                            null=True
                        )

class FlyerImages(MyBaseModel):

    flyer_scheduler_id = models.ForeignKey(
                                FlyerScheduler, 
                                on_delete=models.PROTECT,
                                related_name='Flyer_scheduler'
                            )
    
    sequence = models.IntegerField(
                            default=10,
                            null=False,
                            blank=False
                        )
    
    image = models.ImageField(
                        upload_to=generate_flyer_picture_path,
                        storage=MediaStorage(),
                        validators=[
                            FileExtensionValidator(settings.VALID_IMAGE_FILE_EXTENSIONS), 
                            validate_file_size,
                            validate_file_authenticity,
                            validate_file_infection
                        ],
                        blank=False,
                        null=False,
                        verbose_name='Flyer_picture'
                    )
    
    learn_more_url = models.TextField(
                                max_length=500, 
                                blank=True, 
                                null=True
                            )
    
    learn_more_url_text = models.CharField(
                                    max_length=30,
                                    blank=True,
                                    null=True
                                )
    
    learn_more_url_color = models.CharField(
                                    max_length=10,
                                    blank=True,
                                    null=True
                                )
    
    created_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            related_name='create_by_base_user',
                            blank=True,
                            null=True
                        )
    
    updated_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            related_name='update_by_base_user',
                            blank=True,
                            null=True
                        )