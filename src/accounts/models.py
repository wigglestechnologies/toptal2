from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken

# Create your models here.

class AccountManager(BaseUserManager):

    def create_user(self, first_name, last_name, email, password):
        
        if not first_name:
            raise ValueError('Users must have a first name')
        
        if not last_name:
            raise ValueError('Users must have a last name')

        if not email:
            raise ValueError('Users must have an email address')

        if not password:
            raise ValueError('Users must have a password')

        user = self.model(email=self.normalize_email(email), first_name=first_name, last_name=last_name)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, first_name, last_name, email, password):
        
        user = self.create_user(first_name, last_name, email, password)

        user.is_staff = True
        user.save(using=self._db)
        return user
    
    def create_superuser(self, first_name, last_name, email, password):

        user = self.create_user(first_name, last_name, email, password)
        
        user.is_active      = True
        user.is_verified    = True
        user.is_staff       = True        
        user.is_admin       = True
        user.is_superuser   = True
        
        user.save(using=self._db)
        return user

class Account(AbstractBaseUser):

    email               = models.EmailField(verbose_name='email', max_length=60, unique=True)
    first_name          = models.CharField(verbose_name='firstname', max_length=100, default="")
    last_name           = models.CharField(verbose_name='lastname', max_length=100, default="")
    date_joined         = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login          = models.DateTimeField(verbose_name="last login", auto_now=True)
    login_attempt_count = models.IntegerField(verbose_name="login_attempt_count", default=0)
            
    is_verified     = models.BooleanField(default=False)    
    is_active       = models.BooleanField(default=True)    
    is_staff        = models.BooleanField(default=False) 
    is_admin        = models.BooleanField(default=False)
    is_superuser    = models.BooleanField(default=False)
       
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name'] 

    objects = AccountManager()
    
    def __str__(self): 
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True   

    def tokens(self):
        
        refresh = RefreshToken.for_user(self)
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)            
        }