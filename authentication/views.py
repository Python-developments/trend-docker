from .models import CustomUser, Block
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from .permissions import IsBlockerSelf
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import BlockListSerializer, MyTokenObtainPairSerializer, CustomUserRegistrationSerializer,  ResetPasswordEmailSerializer, VerifyOtpCodeSerializer, SetNewPasswordSerializer, BlockSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError




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


