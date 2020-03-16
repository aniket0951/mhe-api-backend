from import_export import resources

from utils.serializers import DynamicFieldsModelSerializer

from .models import (Country, Gender, IDProof, MaritalStatus, Nationality,
                     Province, Region, Relation, Religion, Speciality, Title)


class ProvinceSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Province
        exclude = ('created_at', 'updated_at',)

class RegionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Region
        exclude = ('created_at', 'updated_at',)


class CountrySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Country
        exclude = ('created_at', 'updated_at',)

class IDProofSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = IDProof
        exclude = ('created_at', 'updated_at',)

class TitleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Title
        exclude = ('created_at', 'updated_at',)


class NationalitySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Nationality
        exclude = ('created_at', 'updated_at',)


class SpecialitySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Speciality
        exclude = ('created_at', 'updated_at',)


class ReligionSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Religion
        exclude = ('created_at', 'updated_at',)


class RelationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Relation
        exclude = ('created_at', 'updated_at',)


class MaritalStatusSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = MaritalStatus
        exclude = ('created_at', 'updated_at',)


class GenderSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Gender
        exclude = ('created_at', 'updated_at',)
