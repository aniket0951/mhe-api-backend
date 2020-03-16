from import_export import resources


from .models import (Country, Gender, IDProof, MaritalStatus, Nationality,
                     Province, Region, Relation, Religion, Speciality, Title)


class TitleResource(resources.ModelResource):
    class Meta:

        model = Title


class NationalityResource(resources.ModelResource):

    class Meta:
        model = Nationality


class SpecialityResource(resources.ModelResource):
    class Meta:

        model = Speciality


class ReligionResource(resources.ModelResource):

    class Meta:
        model = Religion


class RelationResource(resources.ModelResource):
    class Meta:

        model = Relation


class MaritalStatusResource(resources.ModelResource):
    class Meta:

        model = MaritalStatus


class GenderResource(resources.ModelResource):
    class Meta:
        model = Gender


class ProvinceResource(resources.ModelResource):
    class Meta:
        model = Province


class RegionResource(resources.ModelResource):
    class Meta:
        model = Region


class CountryResource(resources.ModelResource):
    class Meta:
        model = Country


class IDProofResource(resources.ModelResource):
    class Meta:
        model = IDProof
