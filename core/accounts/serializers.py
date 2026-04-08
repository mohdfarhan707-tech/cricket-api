from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.strip().lower()

    def validate_username(self, value: str) -> str:
        v = value.strip()
        if not v:
            raise serializers.ValidationError("Username is required.")
        if User.objects.filter(username__iexact=v).exists():
            raise serializers.ValidationError("This username is already taken.")
        return v

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )


class LoginSerializer(serializers.Serializer):
    """Accept email or username in one field."""

    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)
