from accounts.api.views import (ChangePasswordAPIView,
                                EmailVerifyAPIView, LoginAPIView,
                                PasswordResetAPIView,
                                RequestPasswordResetEmailAPIView,
                                SetNewPasswordAPIView,
                                LogoutAPIView, LogoutAllAPIView, AccountRUDAPIView,
                                ListCreateAccountAPIView
                                )
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

app_name = 'accounts'

urlpatterns = [
    path('', ListCreateAccountAPIView.as_view(), name='list-create-user'),    
    path('<int:id>/', AccountRUDAPIView.as_view(), name='rud-user'),    
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('logout-all/', LogoutAllAPIView.as_view(), name='logout-all'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change-password'),
    path('request-password-reset/', RequestPasswordResetEmailAPIView.as_view(),
         name='request-password-reset'),
    path('password-reset/<uidb64>/<token>/',
         PasswordResetAPIView.as_view(), name='password-reset'),
    path('set-password/', SetNewPasswordAPIView.as_view(), name='set-password'),
    path('email-verify/', EmailVerifyAPIView.as_view(), name='email-verify'),    
]