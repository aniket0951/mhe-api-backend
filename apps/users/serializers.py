from apps.users.models import BaseUser, Relationship
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseUser
        fields = ['id', 'first_name', 'last_name', 'middle_name',
                  'mobile', 'facebook_id', 'google_id', 'email']
