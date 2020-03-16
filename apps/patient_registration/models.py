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


class Country(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)
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
    class Meta:
        verbose_name = "Province"
        verbose_name_plural = "Province"

    def __str__(self):
        return self.code