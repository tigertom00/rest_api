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
            "chat_session_id",
            "language",
        )
        read_only_fields = (
            "id",
            "email",
            "date_joined",
            "last_login",
            "chat_session_id",
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
