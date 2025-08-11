from rest_framework import serializers
from .models import Task
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'user', 'description', 'status', 'priority', 
            'due_date', 'estimated_time', 'completed', 'completed_at',
            'clerk_user_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name', 'date_of_birth',
            'address', 'city', 'country', 'website', 'phone', 
            'profile_picture', 'clerk_profile_image_url', 'dark_mode',
            'clerk_id', 'has_image', 'two_factor_enabled', 'clerk_updated_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'clerk_updated_at']