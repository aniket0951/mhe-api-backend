from django.db import models

from apps.health_packages.models import HealthPackage
from apps.lab_and_radiology_items.models import LabRadiologyItem
from apps.master_data.models import Hospital
from apps.meta_app.models import MyBaseModel
from apps.patients.models import Patient


class HealthPackageCart(MyBaseModel):

    patient_info = models.OneToOneField(Patient,
                                        on_delete=models.PROTECT,
                                        null=False,
                                        blank=False,
                                        related_name='patient_health_package_cart')

    health_packages = models.ManyToManyField(HealthPackage,
                                             blank=True)

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 null=False,
                                 blank=False)

    @property
    def representation(self):
        return 'Patient: {}'.format(self.patient_info.first_name)

    class Meta:
        verbose_name = "Health Package Cart"
        verbose_name_plural = "Health Packages Cart"

    def __str__(self):
        return self.representation


class HomeCollectionCart(MyBaseModel):

    patient_info = models.OneToOneField(Patient,
                                        on_delete=models.PROTECT,
                                        null=False,
                                        blank=False,
                                        related_name='patient_home_collection_cart')

    home_collections = models.ManyToManyField(LabRadiologyItem,
                                              blank=True)

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 null=False,
                                 blank=False)

    @property
    def representation(self):
        return 'Patient: {}'.format(self.patient_info.first_name)

    class Meta:
        verbose_name = "Home Collection Cart"
        verbose_name_plural = "Home Collections Cart"

    def __str__(self):
        return self.representation
