from rest_framework import serializers
from .models import Notification
from authentication.models import CustomUser


class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    sender_user_id = serializers.IntegerField(source="sender.id", read_only=True)
    sender_avatar = serializers.SerializerMethodField()
    reaction_type = serializers.CharField(source="reactions.reaction_type", read_only=True)
    follow_notification = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    post_id = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'user_id', 'post_id', 'sender_username', 'sender_user_id', 'sender_avatar',
            'notification_type', 'created_at', 'is_read', 'reaction_type', 'follow_notification'
        ]

    def get_sender_avatar(self, obj):
        if obj.sender.avatar:
            return obj.sender.avatar.url
        return None

    def get_follow_notification(self, obj):
        return Notification.objects.filter(
            user=obj.user, sender=obj.sender, notification_type='follow'
        ).exists()

    def get_post_id(self, obj):
        try:
            return obj.reactions.post.id
        except AttributeError:
            return None


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'avatar']
