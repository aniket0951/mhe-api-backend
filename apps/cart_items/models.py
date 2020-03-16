from django.db import models

from apps.health_packages.models import HealthPackage
from apps.meta_app.models import MyBaseModel
from apps.patients.models import Patient
from apps.master_data.models import Hospital


class HealthPackageCart(MyBaseModel):

    patient_info = models.OneToOneField(Patient,
                                        on_delete=models.PROTECT,
                                        null=False,
                                        blank=False,
                                        related_name='patient_health_package_cart')

    health_packages = models.ManyToManyField(HealthPackage,
                                             null=True,
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
