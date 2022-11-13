from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import (AuthenticationFailed, NotAuthenticated,
                                       ValidationError)

from core.models import User


class PasswordField(serializers.CharField):

    def __init__(self, **kwargs):
        kwargs['style'] = {'input_type': 'password'}
        kwargs.setdefault('write_only', True)
        super().__init__(**kwargs)
        self.validators.append(validate_password)


class CreateUserSerializer(serializers.ModelSerializer):
    password = PasswordField(required=True)
    password_repeat = PasswordField(required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password', 'password_repeat']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_repeat']:
            raise ValidationError('Passwords must match')
        return attrs

    def create(self, validated_data):
        del validated_data['password_repeat']
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = PasswordField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        if not (user := authenticate(
            username=validated_data['username'],
            password=validated_data['password'],
        )):
            raise AuthenticationFailed
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class UpdatePasswordSerializer(serializers.Serializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    old_password = PasswordField(required=True)
    new_password = PasswordField(required=True)

    def validate(self, attrs):
        if not (user := attrs['user']):
            raise NotAuthenticated
        if not user.check_password(attrs['old_password']):
            raise ValidationError({'old_password': 'field is incorrect'})
        return attrs

    def create(self, validated_data):
        raise NotImplementedError

    def update(self, instance, validated_data):
        instance.password = make_password(validated_data['new_password'])
        instance.save()
        return instance
