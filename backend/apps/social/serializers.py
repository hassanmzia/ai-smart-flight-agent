from rest_framework import serializers
from .models import UserContact


class UserContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserContact
        fields = [
            'id', 'name', 'city', 'country', 'address', 'phone', 'email',
            'relationship', 'notes', 'latitude', 'longitude',
            'invite_status', 'invite_code',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'latitude', 'longitude', 'invite_code', 'created_at', 'updated_at']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('Name cannot be empty.')
        return value.strip()

    def validate_city(self, value):
        if not value.strip():
            raise serializers.ValidationError('City is required.')
        return value.strip()
