from rest_framework import serializers
from .models import Profile, Follow
from post.models import Post, HiddenPost
# from vlog.models import Video
from authentication.pagination import CustomPageNumberPagination

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', 'content', 'created_at', 'updated_at', 'image')

class ProfileSerializer(serializers.ModelSerializer):
    user_posts = serializers.SerializerMethodField(read_only=True)  # For list view only
    posts_count = serializers.SerializerMethodField(read_only=True)
    followers_count = serializers.SerializerMethodField(read_only=True)
    following_count = serializers.SerializerMethodField(read_only=True)
    is_following = serializers.SerializerMethodField(read_only=True)

    bio = serializers.CharField(allow_blank=True, required=False)  # Editable in update
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    location = serializers.CharField(allow_blank=True, required=False)

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

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
        instance.bio = validated_data.get('bio', instance.bio)
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.location = validated_data.get('location', instance.location)
        instance.save()
        return instance

    class Meta:
        model = Profile
        fields = (
            'id', 'username', 'first_name', 'last_name', 'bio', 'email', 'avatar',
            'location', 'posts_count', 'followers_count', 'following_count',
            'is_following', 'user_posts', 'hide_avatar', 'created_at', 'updated_at',
        )


class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.CharField(source='follower.username', read_only=True)
    following = serializers.CharField(source='following.username', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']

# class ProfileUpdateSerializer(serializers.ModelSerializer):

#     bio = serializers.CharField(allow_blank=True, required=False)
#     avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
#     first_name = serializers.CharField(source='user.first_name', read_only=True)
#     last_name = serializers.CharField(source='user.last_name', read_only=True)
#     location = serializers.CharField(allow_blank=True, required=False)
#     email = serializers.EmailField(source='user.email', read_only=True)
#     username = serializers.CharField(source='user.username', read_only=True)

#     def validate_avatar(self, value):
#         if value.size > 5 * 1024 * 1024:
#             raise serializers.ValidationError("Avatar file size exceeds 5 MB.")
#         return value

#     class Meta:
#         model = Profile
#         fields = ('bio', 'avatar', 'first_name', 'last_name', 'email', 'username', 'location')

#     def update(self, instance, validated_data):
#         instance.bio = validated_data.get('bio', instance.bio)
#         instance.avatar = validated_data.get('avatar', instance.avatar)
#         instance.location = validated_data.get('location', instance.location)
#         instance.save()
#         return instance