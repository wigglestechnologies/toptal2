from accounts.models import Account
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.exceptions import (AuthenticationFailed, ParseError,
                                       PermissionDenied, ValidationError)
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .serializers import (AccountFullSerializer, ChangePasswordSerializer,
                          LoginSerializer, RegistrationSerializer, RequestPasswordEmailSerializer, SetNewPasswordSerializer,
                          LogoutSerializer, AccountBasicSerializer)

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.reverse import reverse as api_reverse

from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken, BlacklistedToken
import jwt

from django.conf import settings

from common.utils import send_mail

from accounts.signals import user_logged_in

from .permissions import IsAdminOrSelf

from .validators import ValidatePassword
    
def InvalidatedAllUserTokens(user_id):
    tokens = OutstandingToken.objects.filter(user_id=user_id)
    for token in tokens:            
        t, _ = BlacklistedToken.objects.get_or_create(token=token)

class LoginAPIView(GenericAPIView):

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        
        serializer = LoginSerializer(data=request.data)        
        
        serializer.is_valid(raise_exception=True)                
        
        user = Account.objects.get(email=serializer.validated_data['email'])
        if not user:
            Response(status=status.HTTP_404_NOT_FOUND)

        # notify listeners
        user_logged_in.send(sender=self.__class__, user_id=user.pk)
      
        data = {
            'id': user.pk, 
            'email': user.email,
            'tokens': user.tokens()
            }

        return Response(data=data)

class ChangePasswordAPIView(GenericAPIView):

    serializer_class = ChangePasswordSerializer
    permission_classes = [AllowAny, IsAuthenticated]

    def put(self, request):
        
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.user = request.user

        serializer.is_valid(raise_exception=True)

        ValidatePassword(serializer.user, serializer.validated_data['password'])
        
        request.user.set_password(serializer.validated_data['password'])
        request.user.save()

        # invalidate old token
        InvalidatedAllUserTokens(request.user.id)
        
        data = {
            'message': f'User id: {request.user.pk} password changed successfully!',
            'tokens': request.user.tokens()
        }
        return Response(data, status=status.HTTP_200_OK)

class ListCreateAccountAPIView(ListCreateAPIView):
        
    queryset = Account.objects.all()

    def get_serializer_class(self):

        if self.request.method == 'POST':
            return RegistrationSerializer
        elif self.request.method == 'GET':
            return AccountBasicSerializer

    def get_permissions(self):

        permission_classes = [IsAdminUser(), ]
        if self.request.method == 'POST':
            permission_classes = [AllowAny(), ]
        
        return permission_classes

    def perform_create(self, serializer):
                
        serializer.is_valid(raise_exception=True)                            
        account = serializer.save()        

        user = Account.objects.get(email=account.email)
        token = jwt.encode({'user_id': str(user.pk)}, settings.SECRET_KEY, algorithm='HS256')

        current_site    = get_current_site(request=self.request).domain         
        relative_link   = api_reverse('accounts-api:email-verify')
        absurl          = 'http://'+current_site+relative_link+'?token='+str(token)
        email_body      = 'Hello, ' + user.first_name + ' click on the link to verify your account.\n\n' + absurl
            
        email_data = {'email_body': email_body, 'email_to': user.email, 'email_subject': 'TopTal Soccer verify account'}
        send_mail(email_data)        
        
        serializer.validated_data['message'] = 'User successfully created. Please verify your e-mail to activate user account.'
       

class AccountRUDAPIView(RetrieveUpdateDestroyAPIView):
    
    queryset = Account.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrSelf]
    lookup_field = "id"
    
    def get_serializer_class(self):
        
        if self.request.user.is_admin:
            return AccountFullSerializer
        else:
            return AccountBasicSerializer

    def perform_destroy(self, serializer):
        
        if not self.request.user.is_admin:
            raise PermissionDenied("You can't delete your account. Contact admin.")   

        serializer.delete()

class RequestPasswordResetEmailAPIView(GenericAPIView):

    serializer_class = RequestPasswordEmailSerializer
    permission_classes = [AllowAny,]

    def post(self, request):
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        if Account.objects.filter(email=email).exists():
            
            user    = Account.objects.get(email=email)
            uidb64  = urlsafe_base64_encode(smart_bytes(user.id))
            token   =  PasswordResetTokenGenerator().make_token(user)

            current_site    = get_current_site(request=request).domain
            relative_link   = api_reverse('accounts-api:password-reset', kwargs={'uidb64': uidb64, 'token': token})
            absurl          = 'http://'+current_site+relative_link
            email_body      = 'Hello, ' + user.first_name + ' click on the link to reset your password.\n\n' + absurl
            
            email_data = {'email_body': email_body, 'email_to': user.email, 'email_subject': 'TopTal Soccer password reset'}
            send_mail(email_data)
            return Response({'message': 'Check your e-mail for the password reset link.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'User not found!'}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetAPIView(GenericAPIView):

    serializer_class = RequestPasswordEmailSerializer
    permission_classes = [AllowAny,]

    def get(self, request, uidb64, token):
        
        try:
            
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = Account.objects.get(id=id)
            
            if PasswordResetTokenGenerator().check_token(user, token):
                return Response({'message': 'Credentials valid!', 'uidb64': uidb64, 'token': token}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Token is invalid! Request new one.'}, status=status.HTTP_400_BAD_REQUEST)                
       
        except DjangoUnicodeDecodeError as identifier:
            if not PasswordResetTokenGenerator().check_token(user, token):                
                return Response({'message': 'Token is invalid! Request new one.'}, status=status.HTTP_400_BAD_REQUEST)
                
class SetNewPasswordAPIView(GenericAPIView):

    serializer_class = SetNewPasswordSerializer
    permission_classes = [AllowAny]

    def put(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        InvalidatedAllUserTokens(self.request.user.id)
        
        data = {'message': 'Password reset success!'}            

        return Response(data, status=status.HTTP_200_OK)

class EmailVerifyAPIView(GenericAPIView):

    def get(self, request):
                
        try:
                        
            token = request.GET.get('token')
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
            user    = Account.objects.get(id=payload['user_id'])

            if not user.is_verified:
                user.is_verified = True
                user.save()

            return Response({'message': 'User successfully activated!'}, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError as e:
            return Response({'message': 'Activation link expired!'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as e:
            return Response({'message': 'Invalid token!'}, status=status.HTTP_400_BAD_REQUEST)

    
class LogoutAPIView(GenericAPIView):
    
    serializer_class = LogoutSerializer
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = RefreshToken(serializer.validated_data['refresh_token'])
        token.blacklist()

        return Response(status=status.HTTP_205_RESET_CONTENT)

class LogoutAllAPIView(GenericAPIView):
    
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        InvalidatedAllUserTokens(request.user.id)
        
        return Response(status=status.HTTP_205_RESET_CONTENT)  
    