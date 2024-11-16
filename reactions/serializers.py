from .models import Reaction
from post.models import Post
from rest_framework import serializers

class ReactionListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    class Meta:
        model = Reaction
        fields = ['id', 'username', 'avatar', 'reaction_type', 'created_at']

