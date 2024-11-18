from rest_framework import serializers
from .models import Post, Comment, HiddenPost
from django.db.models import Count
from reactions.models import Reaction


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
        Add or update a reaction for a post.
        """
        user = validated_data['user']
        post = validated_data['post']
        reaction_type = validated_data['reaction_type']

        # Call the `add_or_update_reaction` method in the Post model
        result = post.add_or_update_reaction(user=user, reaction_type=reaction_type)

        # Add additional fields to the result
        result['post_id'] = post.id
        result['user_name'] = user.username

        return result

    def to_representation(self, instance):
        """
        Customize the response format.
        """
        return instance


    def create(self, validated_data):
        """
        Toggle the reaction for a post.
        """
        user = validated_data['user']
        post = validated_data['post']
        reaction_type = validated_data['reaction_type']

        # Call the toggle_reaction method from the Post model
        result = post.add_or_update_reaction(user=user, reaction_type=reaction_type)

        return result  # Returns {'action': 'added/removed', 'reaction_type': 'type'}


class PostSerializer(serializers.ModelSerializer):
    custom_user_id = serializers.ReadOnlyField(source='user.id')

    username = serializers.CharField(source='user.username', read_only=True)
    profile_id = serializers.ReadOnlyField(source='user.profile.id')
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    like_counter = serializers.SerializerMethodField()
    comment_counter = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()  # Add this field
    total_reaction_count = serializers.SerializerMethodField()
    reactions_list = serializers.SerializerMethodField()
    reaction_list_count = serializers.SerializerMethodField()
    top_3_reactions = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id', 'custom_user_id', 'profile_id', 'username', 'avatar', 'image', 'content',
            'created_at', 'updated_at', 'like_counter', 'comment_counter', 'liked',
            'user_reaction', 'total_reaction_count', 'reactions_list',
            'reaction_list_count', 'top_3_reactions'
        )

    def get_like_counter(self, obj):
        return obj.like_count()

    def get_comment_counter(self, obj):
        return obj.comment_count()

    def get_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_user_reaction(self, obj):
        """
        Retrieve the reaction type of the logged-in user for this post.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            reaction = obj.post_reactions.filter(user=request.user).first()
            return reaction.reaction_type if reaction else None
        return None

    def get_total_reaction_count(self, obj):
        return obj.post_reactions.count()

    def get_reactions_list(self, obj):
        """
        List all reactions with the user and reaction type.
        """
        return [
            {
                "user": reaction.user.username,
                "reaction_type": reaction.reaction_type
            }
            for reaction in obj.post_reactions.select_related('user').all()
        ]

    def get_reaction_list_count(self, obj):
        """
        Count each type of reaction for the post.
        """
        return obj.post_reactions.values('reaction_type').annotate(
            count=Count('reaction_type')
        ).order_by('-count')

    def get_top_3_reactions(self, obj):
        """
        Retrieve the top 3 reactions for the post.
        """
        top_reactions = obj.post_reactions.values('reaction_type').annotate(
            count=Count('reaction_type')
        ).order_by('-count')[:3]

        result = []
        for reaction in top_reactions:
            user = obj.post_reactions.filter(reaction_type=reaction['reaction_type']).first().user.username
            result.append({
                "reaction_type": reaction['reaction_type'],
                "count": reaction['count'],
                "user": user
            })
        return result


    
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
        """
        Ensure that the request has a valid user and post.
        """
        request = self.context.get('request')
        post = self.context.get('post')  # Ensure post is passed explicitly into the serializer context

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        if not post:
            raise serializers.ValidationError("Post instance is required.")

        data['user'] = request.user
        data['post'] = post
        return data


    def create(self, validated_data):
        """
        Toggle the reaction for a post using the Post model's `toggle_reaction` method.
        """
        post = validated_data.pop('post')
        user = validated_data.pop('user')
        reaction_type = validated_data['reaction_type']

        # Use the Post model's toggle_reaction method
        result = post.add_or_update_reaction(user=user, reaction_type=reaction_type)

        # Return a response-like structure for clarity
        if result['action'] == "added":
            return Reaction.objects.filter(post=post, user=user, reaction_type=reaction_type).first()
        elif result['action'] == "removed":
            raise serializers.ValidationError("Reaction removed.")
        else:
            return Reaction.objects.filter(post=post, user=user, reaction_type=reaction_type).first()
