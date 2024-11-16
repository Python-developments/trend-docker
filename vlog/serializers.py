from rest_framework import serializers


from vlog.models import (
    Video, 
    VlogComment, 
    VlogLike,
    VlogReaction,
)


class VideoSerializer(serializers.ModelSerializer):
    like_count = serializers.ReadOnlyField()
    comment_count = serializers.ReadOnlyField()
    author = serializers.CharField(source='author.username', read_only=True)  # Fetch username instead of ID


    class Meta:
        model = Video
        fields = [
            'id',
            'author',
            'title',
            'description',
            'video',
            'duration',
            'thumbnail',
            'created_at',
            'updated_at',
            'like_count',
            'comment_count',
        ]
        read_only_fields = ['author','duration', 'thumbnail', 'created_at', 'updated_at']
        extra_kwargs = {
            "author": {"required": False},
        }
    
class VlogCommentSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    video = serializers.PrimaryKeyRelatedField(
        queryset=Video.objects.all(), 
        required=False
    )

    class Meta:
        model = VlogComment
        fields = ['id', 'video', 'user', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        video_id = self.context['view'].kwargs.get('video_pk')
        validated_data['video_id'] = video_id
        return super().create(validated_data)

class VlogLikeSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    video = serializers.PrimaryKeyRelatedField(queryset=Video.objects.all(), required=False)

    class Meta:
        model = VlogLike
        fields = ['id', 'video', 'user', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        video_id = self.context['view'].kwargs.get('video_pk')
        validated_data['video_id'] = video_id 
        return super().create(validated_data)
    


class VlogReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VlogReaction
        fields = ['reaction_type']
       

    def validate(self, data):
        request = self.context.get('request')
        video_id = request.parser_context.get('kwargs').get('pk')
        data['video'] = video_id
        data['user'] = request.user
        return data

    def create(self, validated_data):
        video_id = validated_data.pop('video')
        user = validated_data.pop('user')
        reaction_type = validated_data['reaction_type']

        try:
            video = Video.objects.get(pk=video_id)
        except Video.DoesNotExist:
            raise serializers.ValidationError("Video not found.")

        # Toggle the reaction
        reaction_exists = VlogReaction.toggle_reaction(video, user, reaction_type)

        if reaction_exists:
            return VlogReaction.objects.get(video=video, user=user, reaction_type=reaction_type)
        else:
            raise serializers.ValidationError("Reaction removed.")
    


