from rest_framework import serializers
# from authentication.models import CustomUser
from .models import Post, Comment, HiddenPost
from reactions.models import Reaction
# from profile_app.serializers import ProfileSerializer

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    custom_user_id = serializers.ReadOnlyField(source='user.id')
    profile_id = serializers.ReadOnlyField(source='user.profile.id')
    avatar = serializers.ImageField(source='user.avatar')

    class Meta:
        model = Comment
        fields = ('id', 'custom_user_id', 'profile_id', 'username', 'avatar', 'content', 'created_at', 'updated_at')

class PostReactionToggleSerializer(serializers.Serializer):
    reaction_type = serializers.ChoiceField(choices=Reaction.REACTION_CHOICES)

    def validate(self, data):
        """
        Ensure that the request has a valid user and post.
        """
        request = self.context.get('request')
        post = self.context.get('post')

        if not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        if not post:
            raise serializers.ValidationError("Post instance is required.")

        data['user'] = request.user
        data['post'] = post
        return data

    def create(self, validated_data):
        """
        Toggle the reaction for a post.
        """
        user = validated_data['user']
        post = validated_data['post']
        reaction_type = validated_data['reaction_type']

        # Call the toggle_reaction method from the Post model
        result = post.toggle_reaction(user=user, reaction_type=reaction_type)

        return result  # Returns {'action': 'added/removed', 'reaction_type': 'type'}


class PostSerializer(serializers.ModelSerializer):
    custom_user_id = serializers.ReadOnlyField(source='user.id')
    username = serializers.CharField(source='user.username', read_only=True)
    profile_id = serializers.ReadOnlyField(source='user.profile.id')
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    like_counter = serializers.SerializerMethodField()
    comment_counter = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    reactions_list = serializers.SerializerMethodField()
    reaction_list_count = serializers.SerializerMethodField()
    total_reaction_count = serializers.SerializerMethodField()
    top_3_reactions = serializers.SerializerMethodField()
    

    class Meta:
        model = Post
        fields = ('id', 'custom_user_id', 'profile_id', 'username', 'avatar', 'image', 'content', 'created_at', 'updated_at', 
                  'like_counter', 'comment_counter', 'liked', 'total_reaction_count','reactions_list', 'reaction_list_count', 'top_3_reactions')

    def get_like_counter(self, obj):
        return obj.like_count()

    def get_comment_counter(self, obj):
        return obj.comment_count()

    def get_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_reactions_list(self, obj):
        return obj.reaction_list()

    def get_reaction_list_count(self, obj):
        return obj.reaction_list_count()
    
    def get_total_reaction_count(self, obj):
        return obj.total_reaction_count() 
    
    def get_top_3_reactions(self, obj):
    # Call get_top_reactions instead of top_reactions_display for structured data
        return obj.get_top_reactions()

    


class LikeToggleSerializer(serializers.Serializer):
    post_id = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())


class CreatePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', 'image', 'content', 'created_at', 'updated_at')

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class CreateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('post', 'content')



class HiddenPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiddenPost
        fields = ['user', 'post']

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ['reaction_type']
        extra_kwargs = {
            'post': {'write_only': True},
            'user': {'write_only': True}
        }

    def validate(self, data):
        request = self.context.get('request')
        post_id = self.context.get('view').kwargs.get('pk')
        user = request.user

        if not user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        post = Post.objects.filter(pk=post_id).first()
        if not post:
            raise serializers.ValidationError("Post not found.")

        data['post'] = post
        data['user'] = user
        return data

    def create(self, validated_data):
        """
        Toggle the reaction for a post using the Post model's `toggle_reaction` method.
        """
        post = validated_data.pop('post')
        user = validated_data.pop('user')
        reaction_type = validated_data['reaction_type']

        # Use the Post model's toggle_reaction method
        result = post.toggle_reaction(user=user, reaction_type=reaction_type)

        # Return a response-like structure for clarity
        if result['action'] == "added":
            return Reaction.objects.filter(post=post, user=user, reaction_type=reaction_type).first()
        elif result['action'] == "removed":
            raise serializers.ValidationError("Reaction removed.")
        else:
            return Reaction.objects.filter(post=post, user=user, reaction_type=reaction_type).first()
