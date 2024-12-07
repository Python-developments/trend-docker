from rest_framework import serializers
from .models import Profile, Follow
from post.models import Post, HiddenPost
from authentication.pagination import CustomPageNumberPagination
from post.serializers import PostSerializer

class ProfileSerializer(serializers.ModelSerializer):
    user_posts = serializers.SerializerMethodField(read_only=True)  
    posts_count = serializers.SerializerMethodField(read_only=True)
    followers_count = serializers.SerializerMethodField(read_only=True)
    following_count = serializers.SerializerMethodField(read_only=True)
    is_following = serializers.SerializerMethodField(read_only=True)

    bio = serializers.CharField(allow_blank=True, required=False)  
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    location = serializers.CharField(allow_blank=True, required=False)

    username = serializers.CharField(source='user.username', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    phone_number = serializers.CharField(source='user.phone_number', required=False)

    def get_user_posts(self, profile):
        user = self.context['request'].user
        posts = Post.objects.filter(user=profile.user).order_by('-created_at')
        if user.is_authenticated:
            hidden_post_ids = HiddenPost.objects.filter(user=user).values_list('post_id', flat=True)
            posts = posts.exclude(id__in=hidden_post_ids)
        paginator = CustomPageNumberPagination()
        page = paginator.paginate_queryset(posts, self.context['request'])
        post_serializer = PostSerializer(page, many=True, context=self.context)
        return post_serializer.data

    def get_posts_count(self, profile):
        """Return the count of posts for the profile."""
        return Post.objects.filter(user=profile.user).count()

    def get_followers_count(self, profile):
        return profile.user.followers.count()

    def get_following_count(self, profile):
        return profile.user.following.count()

    def get_is_following(self, profile):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=profile.user).exists()
        return False

    def update(self, instance, validated_data):
        user_data = validated_data.get('user', {})
        user = instance.user

        # Update user fields if provided
        if 'phone_number' in user_data:
            user.phone_number = user_data['phone_number']
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        user.save()

        # Update profile fields if provided
        if 'bio' in validated_data:
            instance.bio = validated_data['bio']
        if 'avatar' in validated_data:
            instance.avatar = validated_data['avatar']
        if 'location' in validated_data:
            instance.location = validated_data['location']
        instance.save()

        return instance

    class Meta:
        model = Profile
        fields = (
            'id', 'username', 'first_name', 'last_name', 'bio', 'email', 'phone_number',
            'avatar', 'location', 'posts_count', 'followers_count', 'following_count',
            'is_following', 'user_posts', 'hide_avatar', 'created_at', 'updated_at',
        )


class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.CharField(source='follower.username', read_only=True)
    following = serializers.CharField(source='following.username', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
