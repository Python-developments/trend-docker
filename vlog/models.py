import os
import tempfile
import logging
from django.conf import settings
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from moviepy.editor import VideoFileClip
from authentication.models import CustomUser  # Import your custom user model

# Constants
MAX_VIDEO_SIZE = settings.MAX_VIDEO_SIZE  # Maximum video size in bytes
MAX_VIDEO_DURATION = settings.MAX_VIDEO_DURATION  # Maximum video duration in seconds

# Logger setup
logger = logging.getLogger(__name__)

# Validators
def validate_video_size(file):
    if file.size > MAX_VIDEO_SIZE:
        logger.error(f"Video file size {file.size} exceeds the maximum limit.")
        raise ValidationError(f"Video file size should not exceed {MAX_VIDEO_SIZE / (1024 * 1024)} MB.")

def validate_video_duration(file):
    if isinstance(file, InMemoryUploadedFile):
        # For in-memory uploads, save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_video_path = temp_file.name
    elif isinstance(file, TemporaryUploadedFile):
        # For temporary file uploads, get the file path
        temp_video_path = file.temporary_file_path()
    else:
        raise ValidationError("Unsupported file type for video validation.")

    # Validate duration using VideoFileClip
    try:
        with VideoFileClip(temp_video_path) as video:
            duration = video.duration
            if duration > MAX_VIDEO_DURATION:
                logger.error(f"Video duration {duration} exceeds the maximum limit.")
                raise ValidationError(f"Video duration exceeds the maximum limit of {MAX_VIDEO_DURATION} seconds.")
    finally:
        # Clean up the temporary file if it was created
        if isinstance(file, InMemoryUploadedFile):
            os.remove(temp_video_path)

# Models
class Video(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="videos")
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    video = models.FileField(
        upload_to='vlogs/',
        validators=[
            FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi', 'mkv', 'webm', '3gp']),
            validate_video_size,
            validate_video_duration
        ]
    )
    duration = models.DurationField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new:
                # Create a video thumbnail using Celery
                from vlog.tasks import create_video_thumbnail
                transaction.on_commit(
                    lambda: create_video_thumbnail.delay(self.pk)
                )

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

class VlogComment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vlog_comments')
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}..."

class VlogLike(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vlog_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('video', 'user')  # Ensure unique likes per user per video

    def __str__(self):
        return f"{self.user.username} liked video {self.video.id}"

class VlogReaction(models.Model):
    REACTION_CHOICES = [
        ('love', '❤️ Love'),
        ('like', '👍 Like'),
        ('haha', '😂 Haha'),
        ('wow', '😮 Wow'),
        ('crying', '😭 Crying'),
        ('disgusting', '🤮 Disgusting'),
    ]

    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vlog_reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('video', 'user', 'reaction_type')  # Ensure unique reaction type per user per video

    def __str__(self):
        return f"{self.user.username} reacted {self.get_reaction_type_display()} to video {self.video.id}"

    @classmethod
    def toggle_reaction(cls, video, user, reaction_type):
        """
        Toggle a reaction. If the reaction exists, remove it. Otherwise, create it.
        """
        try:
            reaction = cls.objects.get(video=video, user=user, reaction_type=reaction_type)
            reaction.delete()
            return False  # Reaction was removed
        except cls.DoesNotExist:
            cls.objects.create(video=video, user=user, reaction_type=reaction_type)
            return True  # Reaction was added
