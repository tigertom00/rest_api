from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.validators import UniqueValidator
import random

Users = get_user_model()


#* Users Serializer
class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = (
            'id', 'email', 'display_name', 'first_name', 'last_name', 'date_of_birth', 'address',
            'city', 'country', 'website', 'phone', 'profile_picture', 'date_joined', 'last_login', 'dark_mode'
        )
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False}
        }
        # fields = '__all__'
        # queryset = Users.objects.all()

#* Create Users Serializer

class CreateUsersSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=Users.objects.all(), message="A user with that email already exists.")]
    )
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Users
        fields = ('email', 'password1', 'password2',)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match")
        validate_password(data['password1'])
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        email = validated_data['email'].lower()
        user = Users.objects.create_user(
            email=email,
            password=validated_data['password1'],
        )
        return user
    

#* Custom Token Obtain Pair Serializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super(MyTokenObtainPairSerializer, cls).get_token(user)


        # Add custom claims
        # token['name'] = user.name
        # ...

        return token


class TokenObtainLifetimeSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['lifetime'] = int(refresh.access_token.lifetime.total_seconds())
        return data


class TokenRefreshLifetimeSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = RefreshToken(attrs['refresh'])
        data['lifetime'] = int(refresh.access_token.lifetime.total_seconds())
        return data

#* Blacklist Token Serializer
class BlacklistTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
