from import_export import resources

from utils.serializers import DynamicFieldsModelSerializer

from .models import (City, Country, Gender, IDProof, MaritalStatus,
                     Nationality, Province, Region, Relation, Religion,
                     Speciality, Title, Zipcode)


class CountrySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Country
        exclude = ('created_at', 'updated_at',)
        extra_kwargs = {
            'from_date': {'write_only': True, },
            'to_date': {'write_only': True, },
            'is_active': {'write_only': True, },
        }


class RegionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Region
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        response_object['country'] = CountrySerializer(instance.country).data
        return response_object


class ProvinceSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Province
        exclude = ('created_at', 'updated_at',)


class CitySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = City
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        response_object['region'] = RegionSerializer(
            instance.province.region).data
        return response_object


class ZipcodeSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Zipcode
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        response_object['city'] = CitySerializer(instance.city).data
        return response_object


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
