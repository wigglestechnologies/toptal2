import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse as api_reverse
from rest_framework.test import APITestCase

from accounts.api.serializers import AccountFullSerializer

from accounts.api.consts import MAX_USER_LOGIN_ATTEMPTS

User = get_user_model()

class RegistrationTestCase(APITestCase):

    def test_registration_no_required_fields(self):

        data = {
            'email': 'aa@aa.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'password': 'abc1234',
        }

        url = api_reverse('accounts-api:list-create-user')
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_pass_no_match(self):

        data = {
            'email': 'aa@aa.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'password': 'abc1234',
            'password2': 'abc123'
        }

        url = api_reverse('accounts-api:list-create-user')
        response = self.client.post(url, data=data)        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_ok(self):

        data = {
            'email': 'aa@aa.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'password': 'abc1234',
            'password2': 'abc1234'
        }

        url = api_reverse('accounts-api:list-create-user')
        response = self.client.post(url, data=data)        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_user_exists(self):

        data = {
            'email': 'aa@aa.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'password': 'abc1234',
            'password2': 'abc1234'
        }

        url = api_reverse('accounts-api:list-create-user')
        response = self.client.post(url, data=data)        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(url, data=data)        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class LoginTestCase(APITestCase):

    def setUp(self):

        self.admin_user         = User.objects.create_superuser('John', 'Admin', 'admin@soccer.com', 'abc1234')

        self.unverified_user    = User.objects.create_user('John', 'Unverified', 'unverified@soccer.com', 'abc1234')
        
        self.verified_user      = User.objects.create_user('John', 'Verified', 'verified@soccer.com', 'abc1234')
        self.verified_user.is_verified = True
        self.verified_user.save()

    def test_login_unverified(self):

        data = {
            'email': self.unverified_user.email,
            'password': 'abc1234'
        }
        
        url = api_reverse('accounts-api:login')
        response = self.client.post(url, data=data)        

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_verified(self):

        data = {
            'email': self.verified_user.email,
            'password': 'abc1234'
        }
        
        url = api_reverse('accounts-api:login')
        response = self.client.post(url, data=data)        

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_lock_attempts(self):

        url = api_reverse('accounts-api:login')
        data = {
            'email': self.verified_user.email,
            'password': 'abc1233'
        }
        
        # wrong password one time        
        response = self.client.post(url, data=data)        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # right password, expect success
        data['password'] = 'abc1234'
        response = self.client.post(url, data=data)        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # lock account
        data['password'] = 'abc1233'
        for i in range(MAX_USER_LOGIN_ATTEMPTS):
            response = self.client.post(url, data=data)        
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # try to login, expect failure
        data['password'] = 'abc1234'
        response = self.client.post(url, data=data)        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # admin unlock the account
        data_admin = {'is_active': 'True'}        
        response = self.client.patch(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.verified_user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],
            data=data_admin
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # try to login again, expect success        
        response = self.client.post(url, data=data)        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class NormalUserCRUDUsersTestCase(APITestCase):

    def setUp(self):        
        
        self.admin_user         = User.objects.create_superuser('John', 'Admin', 'admin@soccer.com', 'abc1234')        
        self.user               = User.objects.create_user('John', 'User', 'userr@soccer.com', 'abc1234')
        self.user.is_verified = True
        self.user.save()

    def test_admin_update_admin(self):

        data = {'last_name': 'Test', 'is_verified': 'False'}        
        response = self.client.patch(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.admin_user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],
            data=data
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['last_name'], 'Test')
        self.assertEqual(response.data['is_verified'], False)

    def test_admin_retrieve_admin(self):
        
        response = self.client.get(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.admin_user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access']
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_delete_admin(self):
        
        response = self.client.delete(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.admin_user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access']
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_update_admin(self):

        data = {'last_name': 'Test'}
        response = self.client.patch(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.admin_user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_update_user(self):

        data = {'last_name': 'Test', 'is_admin': 'True'}        
        response = self.client.patch(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['last_name'], 'Test')
        self.assertEqual(response.data['is_admin'], False)


    def test_user_retrieve_admin(self):
        
        response = self.client.get(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.admin_user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access']
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_retrieve_self(self):
        
        response = self.client.get(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access']
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_delete_admin(self):
        
        response = self.client.delete(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.admin_user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access']
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete_user(self):
        
        response = self.client.delete(
            api_reverse('accounts-api:rud-user', kwargs={'id': str(self.user.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access']
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class NormalUserChangePassword(APITestCase):

    def setUp(self):               
        
        self.user               = User.objects.create_user('John', 'User', 'userr@soccer.com', 'abc1234')
        self.user.is_verified = True
        self.user.save()

    def test_user_change_password(self):
        
        url = api_reverse('accounts-api:change-password') 

        data = {
            'old_password': 'abc1234', 
            'password': 'abc101112', 
            'password2': 'abc101112',             
            }

        response = self.client.put(url, data=data, HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'])        
        self.assertEqual(response.status_code, status.HTTP_200_OK)        

    def test_user_change_password_wrong_old_password(self):
        
        url = api_reverse('accounts-api:change-password')
        
        data = {
            'old_password': 'abc12346', 
            'password': 'abc101112', 
            'password2': 'abc101112',             
            }
        response = self.client.put(url, data=data, HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'])        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)        

    def test_user_change_password_wrong_new_password_mismatch(self):
        
        url = api_reverse('accounts-api:change-password')
        
        data = {
            'old_password': 'abc1234', 
            'password': 'abc1011126', 
            'password2': 'abc101112',             
            }
        response = self.client.put(url, data=data, HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'])        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)        