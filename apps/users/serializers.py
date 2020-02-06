from rest_framework import serializers
from apps.users.models import BaseUser, Relationship

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseUser
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'mobile', 'otp', 'facebook_id', 'google_id']
