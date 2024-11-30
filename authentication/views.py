from random import SystemRandom
import requests
from urllib.parse import urlencode, urljoin
from oauthlib.common import UNICODE_ASCII_CHARACTER_SET

from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
from django.urls import reverse

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from drf_yasg.utils import swagger_auto_schema


from .serializers import BlockListSerializer, MyTokenObtainPairSerializer, CustomUserRegistrationSerializer,  ResetPasswordEmailSerializer, VerifyOtpCodeSerializer, SetNewPasswordSerializer, BlockSerializer
from .models import CustomUser, Block
from .permissions import IsBlockerSelf

# login
class MyTokenObtainPairSerializer(TokenObtainPairView):

    serializer_class = MyTokenObtainPairSerializer


class UserRegisterView(CreateAPIView):

    serializer_class = CustomUserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        '''
        POST Method

        Overrides the post method to handle user registration.
        '''
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            response_data = {
                'response': 'Successfully registered new user.',
                'email': serializer.data['email'],
                'username': serializer.data['username'],
                'avatar': serializer.data['avatar'],
            }
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# CRUD
class DisplayList(generics.ListCreateAPIView):
    '''
    User List and Create View

    This view displays a list of users and handles user creation in our project.
    '''
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserRegistrationSerializer


class DisplayDetail(generics.RetrieveUpdateDestroyAPIView):

    '''
    User Detail View

    This view displays, updates, and deletes individual user instances in our project.
    '''
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserRegistrationSerializer


# forgot password views
class PasswordResetRequestView(APIView):

    @swagger_auto_schema(request_body=ResetPasswordEmailSerializer)
    def post(self, request):
        serializer = ResetPasswordEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            try:
                user = CustomUser.objects.get(email=email)
                user.generate_otp()
                user.send_password_reset_email()
                return Response({"success": True}, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                return Response({"success": False, "message": "The account was not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOtpCodeView(APIView):
    @swagger_auto_schema(request_body=VerifyOtpCodeSerializer)
    def post(self, request):
        serializer = VerifyOtpCodeSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"success": True}, status=status.HTTP_200_OK)
        return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordView(APIView):
    @swagger_auto_schema(request_body=SetNewPasswordSerializer)
    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            new_password = serializer.validated_data.get('new_password')
            user = CustomUser.objects.get(email=email)
            user.set_password(new_password)
            # user.last_otp = None
            # user.otp_expiry = None
            user.save()
            return Response({"success": True}, status=status.HTTP_200_OK)
        return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# blocking views
class BlockCreateView(generics.CreateAPIView):
    """
    View for listing all block relationships or creating a new block relationship.

    Only authenticated users can access this view.
    """
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    permission_classes = [IsBlockerSelf, IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({"success": True, "message": "Block relationship created successfully."}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            message = e.detail if isinstance(e.detail, str) else ' '.join([str(item) for sublist in e.detail.values() for item in sublist])
            return Response({"success": False, "message": message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        serializer.save()


class BlockListView(generics.ListAPIView):
    """
    View for listing all block relationships.

    Only authenticated users can access this view.
    """
    serializer_class = BlockListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns blocks for the authenticated user.
        """
        user = self.request.user
        return Block.objects.filter(blocker=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True,  context={'request': request})
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)


class UnblockUserView(generics.DestroyAPIView):
    """
    View for unblocking a user.

    Only authenticated users can access this view.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        blocker = request.user
        blocked_id = kwargs.get('blocked_id')  # Get blocked user's ID from URL

        # Fetch the block relationship to delete
        block = get_object_or_404(Block, blocker=blocker, blocked_id=blocked_id)

        # Delete the block relationship
        block.delete()

        return Response({"success": True, "message": "User unblocked successfully."}, status=status.HTTP_204_NO_CONTENT)


class GoogleLoginRedirectApi(APIView):
    
    def _generate_state_session_token(
        self,
        length=30,
        chars=UNICODE_ASCII_CHARACTER_SET
    ):
        rand = SystemRandom()
        state = "".join(rand.choice(chars) for _ in range(length))
        return state
    
    def get_authorization_url(self):
        state = self._generate_state_session_token()
        SCOPES = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
        ]
        params = {
            "response_type": "code",
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH_CALLBACK_URL,
            "scope": " ".join(SCOPES),
            "state": self._generate_state_session_token(),
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "select_account",
        }

        query_params = urlencode(params)
        authorization_url = f"{settings.GOOGLE_AUTH_URL}?{query_params}"

        return authorization_url, state
    
    def get(self, request, *args, **kwargs):
        authorization_url, state = self.get_authorization_url()
        request.session["google_oauth2_state"] = state
        return redirect(authorization_url)


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL
    client_class = OAuth2Client

    def get_response(self):
        # Call the parent method to get the response from Google
        original_response = super().get_response()
        user = self.request.user  # Get the authenticated user

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Add JWT tokens to the response
        response_data = original_response.data
        response_data['access_token'] = access_token
        response_data['refresh_token'] = refresh_token

        return Response(response_data)


class GoogleLoginCallback(APIView):
    def get(self, request, *args, **kwargs):
        """
        If you are building a fullstack application (eq. with React app next to Django)
        you can place this endpoint in your frontend application to receive
        the JWT tokens there - and store them in the state
        """

        code = request.GET.get("code")

        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        # Remember to replace the localhost:8000 with the actual domain name before deployment
        token_endpoint_url = urljoin("http://localhost:8000", reverse("google_login"))
        response = requests.post(url=token_endpoint_url, data={"code": code})

        return Response(response.json(), status=status.HTTP_200_OK)

# class GoogleLoginCallback(APIView):
#     def get(self, request, *args, **kwargs):
#         """
#         If you are building a fullstack application (eq. with React app next to Django)
#         you can place this endpoint in your frontend application to receive
#         the JWT tokens there - and store them in the state
#         """

#         print("request Get", request.GET)
#         code = request.GET.get("code")

#         if code is None:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
        
#         token_endpoint_url = "https://oauth2.googleapis.com/token"
#         data = {
#             "code": code,
#             "redirect_uri": settings.GOOGLE_OAUTH_CALLBACK_URL,
#             "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
#             "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
#             "grant_type": "authorization_code",
#         }

#         response = requests.post(token_endpoint_url, data=data)

#         # Log the response details
#         print(f"Response Status: {response.status_code}")
#         print(f"Response Content: {response.text}")

#         if response.status_code != 200:
#             return Response(
#                 {"error": "Failed to exchange code for access token", "details": response.text},
#                 status=response.status_code,
#             )

#         try:
#             return Response(response.json(), status=status.HTTP_200_OK)
#         except ValueError as e:
#             return Response(
#                 {"error": "Invalid JSON response", "details": response.text},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )


class FacebookLoginView(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter