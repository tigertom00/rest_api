import random

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from app.memo.models import ElektriskKategori

Users = get_user_model()


# * Users Serializer
class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = (
            "id",
            "email",
            "display_name",
            "first_name",
            "last_name",
            "date_of_birth",
            "address",
            "city",
            "country",
            "website",
            "phone",
            "profile_picture",
            "date_joined",
            "last_login",
            "theme",
            "language",
        )
        read_only_fields = (
            "id",
            "email",
            "date_joined",
            "last_login",
        )


class CreateUsersSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=Users.objects.all(),
                message="A user with that email already exists.",
            )
        ],
    )
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Users
        fields = ("email", "password1", "password2")

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match")
        validate_password(data["password1"])
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        email = validated_data["email"].lower()
        username_base = email.split("@")[0]
        username = username_base
        while Users.objects.filter(username=username).exists():
            username = f"{username_base}{random.randint(1, 10000)}"
        user = Users.objects.create_user(
            email=email, password=validated_data["password1"], username=username
        )
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token


class TokenObtainLifetimeSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data["lifetime"] = int(refresh.access_token.lifetime.total_seconds())
        return data


class TokenRefreshLifetimeSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = RefreshToken(attrs["refresh"])
        data["lifetime"] = int(refresh.access_token.lifetime.total_seconds())
        return data


class BlacklistTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management operations."""

    class Meta:
        model = Users
        fields = (
            "id",
            "email",
            "username",
            "display_name",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "clerk_user_id",
            "two_factor_enabled",
        )
        read_only_fields = (
            "id",
            "date_joined",
            "last_login",
            "clerk_user_id",
        )


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin user update operations."""

    class Meta:
        model = Users
        fields = (
            "is_active",
            "is_staff",
            "is_superuser",
            "display_name",
            "first_name",
            "last_name",
        )


class AdminPasswordResetSerializer(serializers.Serializer):
    """Serializer for admin-initiated password resets."""

    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class UserBasicSerializer(serializers.ModelSerializer):
    """Lightweight user info for use in other app serializers (memo, tasks, etc.)"""

    class Meta:
        model = Users
        fields = ["id", "username", "display_name", "email", "phone", "profile_picture"]
        read_only_fields = fields


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user info including first/last name and computed full name"""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = [
            "id",
            "username",
            "display_name",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "profile_picture",
            "clerk_profile_image_url",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full if full else obj.display_name


# * ElektriskKategori Serializer
class ElektriskKategoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElektriskKategori
        fields = (
            "id",
            "blokknummer",
            "kategori",
            "beskrivelse",
            "slug",
            "etim_gruppe",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ElektriskKategoriCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElektriskKategori
        fields = (
            "blokknummer",
            "kategori",
            "beskrivelse",
            "etim_gruppe",
        )

    def create(self, validated_data):
        return ElektriskKategori.objects.create(**validated_data)
