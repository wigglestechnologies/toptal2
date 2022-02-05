from accounts.models import Account
from rest_framework import serializers
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from .consts import MAX_USER_LOGIN_ATTEMPTS

from .validators import ValidatePassword

class RegistrationSerializer(serializers.ModelSerializer):
    
    message   = serializers.CharField(read_only=True)
    password2 = serializers.CharField(style={'input_type: password'}, write_only=True)
    
    class Meta:
        model = Account
        fields = ['message', 'first_name', 'last_name', 'email', 'password', 'password2']

        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True}}

    def save(self):
        
        account = Account(first_name = self.validated_data['first_name'], 
                          last_name  = self.validated_data['last_name'],
                          email = self.validated_data['email'],                                  
        )

        password  = self.validated_data['password']
        password2 = self.validated_data['password2']

        if password != password2:
            raise serializers.ValidationError({'password': 'Passwords must match.'})

        ValidatePassword(account, password)

        account.set_password(password)
        account.save()

        return account

class AccountFullSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Account
        fields = [
            'id', 
            'first_name', 
            'last_name', 
            'email', 
            'is_admin', 
            'is_active', 
            'is_verified', 
            'date_joined', 
            'last_login'
            ]

        read_only_fields = [
            'id', 
            'email', 
            'date_joined', 
            'last_login'
            ]       

class AccountBasicSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Account
        fields = [
            'id', 
            'first_name', 
            'last_name', 
            'email', 
            'is_admin',             
            'is_active', 
            'is_verified', 
            'date_joined', 
            'last_login'
            ]

        read_only_fields = [
            'id', 
            'email', 
            'date_joined', 
            'last_login',
            'is_admin',
            'is_active',
            'is_verified'
            ]       
        
class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField(max_length=68, write_only=True)    
    password = serializers.CharField(max_length=68, write_only=True)    
    password2 = serializers.CharField(max_length=68, write_only=True)

    user = None
    
    def validate(self, data):
        
        email       = self.user.email
        password    = data['old_password']
                
        user = auth.authenticate(email=email, password=password)
        if not user:
            raise ValidationError('Invalid old password!')
        
        if data['password'] != data['password2']:
            raise ValidationError('Passwords must match!')        

        return data


class LoginSerializer(serializers.Serializer):

    email = serializers.CharField(max_length=60)    
    password = serializers.CharField(max_length=68, write_only=True)    
    tokens = serializers.CharField(max_length=68, read_only=True)
        
    def validate(self, data):
        
        email       = data['email']
        password    = data['password']
                
        user = auth.authenticate(email=email, password=password)        
        
        # user not logged in
        if not user:
            
            try:                
                user = Account.objects.get(email=email)            
            except:
                raise AuthenticationFailed('Invalid user account.')        

            if not user.is_active:
                raise AuthenticationFailed('User inactive! Contact admin.')        
    
            user.login_attempt_count += 1
            if user.login_attempt_count >= MAX_USER_LOGIN_ATTEMPTS:
                
                user.is_active = False
                user.login_attempt_count = 0
                user.save()                    
                raise AuthenticationFailed('Number of login attempts excceded. Contact admin.')    

            else:                    
                
                user.save()
                raise AuthenticationFailed('Invalid user password.')
            
        if not user.is_verified:
            raise AuthenticationFailed('User is not verified! Please check your e-mail for the activation link.')        

        # login successful
        user.login_attempt_count = 0
        user.save()
        
        return super().validate(data)

class RequestPasswordEmailSerializer(serializers.Serializer):

    email = serializers.CharField(max_length=60)

    class Meta:
        fields = ['email']

class SetNewPasswordSerializer(serializers.Serializer):

    password = serializers.CharField(max_length=68, write_only=True)
    token    = serializers.CharField(write_only=True)
    uidb64   = serializers.CharField(write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, data):

        try:
            
            password    = data['password']
            token       = data['token']
            uidb64      = data['uidb64']

            id = force_str(urlsafe_base64_decode(uidb64))
            user = Account.objects.get(id=id)
            
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('Reset link is invalid! Request new one!', 401)

            ValidatePassword(user, password)

            user.set_password(password)
            user.save()

            return super().validate(data)            

        except Exception as e:
            raise AuthenticationFailed('Reset link is invalid! Request new one!', 401)

class LogoutSerializer(serializers.Serializer):
    
    refresh_token = serializers.CharField(max_length=256, write_only=True)

    class Meta:
        fields = ['refresh_token']
        extra_kwargs = {
            'refresh_token': {'required': True}
            }

