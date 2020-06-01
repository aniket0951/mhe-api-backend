from django.db import models

from apps.meta_app.models import MyBaseModel


class Title(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    class Meta:
        verbose_name = "Title"
        verbose_name_plural = "Title"

    def __str__(self):
        return self.code


class Nationality(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    class Meta:
        verbose_name = "Nationality"
        verbose_name_plural = "Nationality"

    def __str__(self):
        return self.code


class Gender(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    class Meta:
        verbose_name = "Gender"
        verbose_name_plural = "Gender"

    def __str__(self):
        return self.code


class MaritalStatus(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    class Meta:
        verbose_name = "Marital Status"
        verbose_name_plural = "Marital Status"

    def __str__(self):
        return self.code


class Relation(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    class Meta:
        verbose_name = "Relation"
        verbose_name_plural = "Relation"

    def __str__(self):
        return self.code


class Religion(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    class Meta:
        verbose_name = "Religion"
        verbose_name_plural = "Religion"

    def __str__(self):
        return self.code


class Speciality(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    class Meta:
        verbose_name = "Speciality"
        verbose_name_plural = "Speciality"

    def __str__(self):
        return self.code


class IDProof(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    class Meta:
        verbose_name = "IDProof"
        verbose_name_plural = "IDProof"

    def __str__(self):
        return self.code


class Language(MyBaseModel):

    description = models.CharField(unique=True,
                                   blank=False,
                                   max_length=300,
                                   null=False)

    translated_description = models.CharField(blank=False,
                                              null=False,
                                              max_length=300)

    from_date = models.DateField(blank=False,
                                 null=False)

    to_date = models.DateField(blank=True,
                               null=True)

    class Meta:
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __str__(self):
        return self.description


class Country(MyBaseModel):

    code = models.CharField(unique=True,
                            blank=False,
                            max_length=30,
                            null=False)

    description = models.CharField(blank=False,
                                   null=False,
                                   max_length=300)

    is_active = models.BooleanField(default=False)

    from_date = models.DateField(blank=False,
                                 null=False)

    to_date = models.DateField(blank=True,
                               null=True)

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Country"

    def __str__(self):
        return self.code


class Region(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    country = models.ForeignKey(
        Country, on_delete=models.PROTECT, related_name='country_region')

    class Meta:
        verbose_name = "Region"
        verbose_name_plural = "Region"

    def __str__(self):
        return self.code


class Province(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name='region_province')

    class Meta:
        verbose_name = "Province"
        verbose_name_plural = "Province"

    def __str__(self):
        return self.code


class City(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    province = models.ForeignKey(
        Province, on_delete=models.PROTECT, related_name='province_city')

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "City"

    def __str__(self):
        return self.code


class Zipcode(MyBaseModel):

    code = models.CharField(blank=False,
                            max_length=100,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    city = models.ForeignKey(
        City, on_delete=models.PROTECT, related_name='city_zipcode')

    class Meta:
        verbose_name = "Zipcode"
        verbose_name_plural = "Zipcode"

    def __str__(self):
        return self.code
