from rest_framework import serializers
from apps.users.models import BaseUser, Relationship

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseUser
<<<<<<< HEAD
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'mobile', 'otp', 'facebook_id', 'google_id']
=======
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'mobile', 'otp', 'facebook_id', 'google_id']
>>>>>>> d6dfac30b99a3c160245cfb84d4b33def833a7f2
