from rest_framework import serializers
from .models import Profile, Follow
from post.models import Post, HiddenPost
from vlog.models import Video
from authentication.pagination import CustomPageNumberPagination

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', 'content', 'created_at', 'updated_at', 'image')

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'video', 'thumbnail', 'duration', 'created_at', 'updated_at')

class ProfileSerializer(serializers.ModelSerializer):
    user_posts = serializers.SerializerMethodField()
    user_videos = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    vlogs_count = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    total_reactions = serializers.SerializerMethodField()

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

    def get_user_videos(self, profile):
        videos = Video.objects.filter(author=profile.user).order_by('-created_at')
        paginator = CustomPageNumberPagination()
        page = paginator.paginate_queryset(videos, self.context['request'])
        video_serializer = VideoSerializer(page, many=True, context=self.context)
        return video_serializer.data

    def get_total_reactions(self, obj):
        return obj.total_reactions()

    def get_posts_count(self, profile):
        return Post.objects.filter(user=profile.user).count()

    def get_followers_count(self, profile):
        return profile.user.followers.count()

    def get_following_count(self, profile):
        return profile.user.following.count()

    def get_vlogs_count(self, profile):
        return Video.objects.filter(author=profile.user).count()

    def get_is_following(self, profile):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=profile.user).exists()
        return False

    class Meta:
        model = Profile
        fields = (
            'id', 'username','first_name','last_name', 'bio', 'avatar', 'background_pic', 'created_at', 'updated_at',
            'posts_count', 'following_count', 'followers_count', 'is_following',
            'user_posts', 'user_videos', 'hide_avatar', 'vlogs_count', 'total_reactions'
        )

class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.CharField(source='follower.username', read_only=True)
    following = serializers.CharField(source='following.username', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']

class ProfileUpdateSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(allow_blank=True, required=False)
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    background_pic = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    def validate_avatar(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Avatar file size exceeds 5 MB.")
        return value

    def validate_background_pic(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Background picture size exceeds 5 MB.")
        return value

    class Meta:
        model = Profile
        fields = ('bio', 'avatar', 'background_pic')

    def update(self, instance, validated_data):
        instance.bio = validated_data.get('bio', instance.bio)
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.background_pic = validated_data.get('background_pic', instance.background_pic)
        instance.save()
        return instance