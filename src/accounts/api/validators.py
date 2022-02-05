
from django.core.exceptions import ValidationError
import django.contrib.auth.password_validation as validators
import soccer.settings
from rest_framework import serializers

def ValidatePassword(user, password):
    
    # if in debug, allow weak passwords
    if soccer.settings.DEBUG:
        return

    errors = dict() 
    try:
        
        # validate the password and catch the exception
        validators.validate_password(user=user, password=password)

    # the exception raised here is different than serializers.ValidationError
    except ValidationError as e:
        errors['password'] = list(e.messages)

    if errors:
        raise serializers.ValidationError(errors)

