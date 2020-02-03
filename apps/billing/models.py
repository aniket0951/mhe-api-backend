from django.db import models
from apps.health_packages.models import HealthPackagePricing
from apps.health_tests.models import HealthTestPricing
from apps.doctors.models import Doctor
from apps.patients.models import Patient
from apps.meta_app.models import MyBaseModel

# Create your models here.

class Visit(MyBaseModel):

    Doctor_id = models.ForeignKey(
            Doctor,
            on_delete=models.PROTECT,
            null=False,
            blank=False)

    patient_id = models.ForeignKey(
            Patient,
            on_delete=models.PROTECT,
            null=False,
            blank=False)

    visit_date = models.DateField()

    test_derived_cost = models.IntegerField()

    class Meta:
        verbose_name = "Visit"
        verbose_name_plural = "Visits"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Visit, self).save(*args, **kwargs)


class VisitTest(MyBaseModel):

    test_id = models.ForeignKey(
            HealthTestPricing,
            on_delete=models.PROTECT,
            null=False,
            blank=False)

    quantity = models.IntegerField(default = 1)

    visit_id = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    total_test_cost = models.IntegerField()

    class Meta:
        verbose_name = "VisitTest"
        verbose_name_plural = "VisitTests"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(VisitTest, self).save(*args, **kwargs)


class VisitHealthPackage(MyBaseModel):

    health_package_id = models.ForeignKey(
            HealthPackagePricing,
            on_delete=models.PROTECT,
            null=False,
            blank=False)

    total_package_cost = models.IntegerField()

    visit_id = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    class Meta:
        verbose_name = "VisitHealthPackage"
        verbose_name_plural = "VisitHealthPackages"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(VisitHealthPackage, self).save(*args, **kwargs)


class VisitAppointment(MyBaseModel):

    appointment_cost = models.IntegerField()

    visit_id = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    class Meta:
        verbose_name = "VisitAppointment"
        verbose_name_plural = "VisitAppointments"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(VisitAppointment, self).save(*args, **kwargs)


class Cart(MyBaseModel):

    visit_id = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    status = models.CharField(max_length = 200)

    class Meta:
        verbose_name = "VisitAppointment"
        verbose_name_plural = "VisitAppointments"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(VisitAppointment, self).save(*args, **kwargs)