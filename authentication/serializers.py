
from django.utils import timezone
from rest_framework import serializers
from profile_app.models import Profile
from profile_app.serializers import ProfileSerializer
from .models import CustomUser, Block
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomUserRegistrationSerializer(serializers.ModelSerializer):
    '''
    Custom User Registration Serializer

    This serializer is used for user registration in our project. It handles validation and creation of new user instances.
    '''

    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'username','first_name','last_name', 'email', 'avatar', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True},
            'password2': {'write_only': True},
        }
        
    def create(self, validated_data):
        '''
        Create Method
        
        Overrides the create method to handle user creation with password hashing and validation.
        '''
        password = validated_data.pop('password')
        password2 = validated_data.pop('password2')
        avatar_data = validated_data.pop('avatar', None)

        if password != password2:
            raise serializers.ValidationError({'Error': 'Passwords must match.'})

        if CustomUser.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError({'Error': 'Email already exists.'})

        if CustomUser.objects.filter(username=validated_data['username']).exists():
            raise serializers.ValidationError({'Error': 'Username already exists.'})

        account = CustomUser(**validated_data)
        account.set_password(password)
        account.save()

        if avatar_data:
            account.avatar = avatar_data
            account.save()

        return account
    
    def update(self, instance, validated_data):
        '''
        Update Method
        
        Overrides the update method to handle updating user avatar.
        '''
        avatar_data = validated_data.get('avatar', None)

        if avatar_data:
            instance.avatar = avatar_data
        instance.save()
        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    '''
    Custom Token Serializer

    This serializer is used for token authentication in our project. It extends the default TokenObtainPairSerializer provided by Django REST Framework SimpleJWT.
    '''

    def validate(self, attrs):
        '''
        Validate Method
        
        Overrides the validate method to include additional user information in the token response.
        '''
        data = super().validate(attrs)
        request = self.context.get('request')
        user = self.user  # get the athenticated user

        # Adds additional user-related information to the token response :
        data['user'] = str(user)
        data['id'] = user.id
        data['email'] = user.email
        
        if user.avatar:
            avatar_url = request.build_absolute_uri(user.avatar.url)
        else:
            avatar_url = None
        data['avatar'] = avatar_url
        data['is_staff'] = user.is_staff
        data['is_active'] = user.is_active
        data['phone_number'] = user.phone_number

        # Retrieve profile_id using the reverse relationship with the profile model
        if hasattr(user, 'profile'):
            profile_instance = user.profile
            if profile_instance:
                data['profile_id'] = profile_instance.id
            else:
                data['profile_id'] = None  # Handle the case where the user has no profile
        else:
            data['profile_id'] = None  # Handle the case where the user has no profile attribute

        return data


class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class VerifyOtpCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            user = CustomUser.objects.get(email=data['email'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if user.last_otp != data['code']:
            raise serializers.ValidationError("Wrong code.")
        
        if user.otp_expiry < timezone.now():
            raise serializers.ValidationError("Code expired.")
        
        return data


class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(max_length=128, validators=[validate_password])

    def validate(self, data):
        try:
            user = CustomUser.objects.get(email=data['email'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if user.last_otp != data['code']:
            raise serializers.ValidationError("Wrong code.")
        
        if user.otp_expiry < timezone.now():
            raise serializers.ValidationError("Code expired.")
        
        return data    


class BlockSerializer(serializers.ModelSerializer):
    blocked_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Block
        fields = ['blocked_id']
        
    def validate(self, data):
        """
        Check that the blocker and blocked users are not the same.
        """
        request = self.context.get('request')
        if request and request.user:
            blocker = request.user
            blocked_id = data.get('blocked_id')
            if blocked_id:
                blocked = CustomUser.objects.get(pk=blocked_id)
                if blocked == blocker:
                    raise serializers.ValidationError("Users cannot block themselves.")
                # Ensure that a block relationship does not already exist before creating a new one
                if Block.objects.filter(blocker=blocker, blocked=blocked).exists():
                    raise serializers.ValidationError("You have already blocked this user.")
                data['blocker'] = blocker
                data['blocked'] = blocked
            else:
                raise serializers.ValidationError("Blocked user ID is required.")
        else:
            raise serializers.ValidationError("Request user is not authenticated.")
        return data


class BlockListSerializer(serializers.ModelSerializer):
    blocked_profile = serializers.SerializerMethodField()

    class Meta:
        model = Block
        fields = ['blocked_profile']

    def get_blocked_profile(self, obj):
        profile = Profile.objects.get(user=obj.blocked)
        return ProfileSerializer(profile, context=self.context).data