from rest_framework import serializers
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']

    def validate(self, data):
        user = self.context['request'].user
        can_create, msg = Project.can_create_project(user)
        if not can_create:
            raise serializers.ValidationError(msg)
        return data


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'created_at', 'is_active']
