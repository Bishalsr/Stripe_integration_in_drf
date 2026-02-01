from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Subscription

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        # Assign FREE plan by default
        Subscription.objects.create(
            user=user,
            plan='free',
            is_active=True
        )
        return user
