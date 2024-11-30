from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    MyTokenObtainPairSerializer, 
    DisplayList, 
    DisplayDetail, 
    PasswordResetRequestView, 
    VerifyOtpCodeView, 
    SetNewPasswordView, 
    UserRegisterView, 
    BlockCreateView, 
    BlockListView, 
    UnblockUserView,
    GoogleLoginRedirectApi,
    GoogleLoginView,
    GoogleLoginCallback,
    FacebookLoginView

)

urlpatterns = [
    # Authentication endpoints
    path('login/', MyTokenObtainPairSerializer.as_view(), name='login'),
    path('token_refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegisterView.as_view(), name='register'),

    # Password reset endpoints
    path('PasswordResetRequest/', PasswordResetRequestView.as_view(), name='PasswordResetRequest'),
    path('VerifyOtp/', VerifyOtpCodeView.as_view(), name='VerifyOtp'),
    path('SetNewPasswordView/', SetNewPasswordView.as_view(), name='SetNewPasswordView'),

    # User display endpoints
    path('users/', DisplayList.as_view(), name='users'),
    path('users/<int:pk>/', DisplayDetail.as_view(), name='user-detail'),

    # Block relationships endpoints
    path('blocks/', BlockListView.as_view(), name='block-list'),
    path('blocks/create/', BlockCreateView.as_view(), name='block-create'),
    path('blocks/unblock/<int:blocked_id>/', UnblockUserView.as_view(), name='unblock-user'),

    # allauth with social auth endpoints
    path("dj_rest_auth/", include("dj_rest_auth.urls")),
    path("allauth/accounts/", include("allauth.urls")),
    path("dj_rest_auth/registration/", include("dj_rest_auth.registration.urls")),
    path("google/redirect/", GoogleLoginRedirectApi.as_view(), name="google_redirect"),
    path("google/login/", GoogleLoginView.as_view(), name="google_login"),
    path(
        "google/callback/",
        GoogleLoginCallback.as_view(),
        name="google_callback",
    ),
    path("facebook-login/", FacebookLoginView.as_view(), name="facebook_login"),
    
]