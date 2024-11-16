# from django.db import models
# from django.utils import timezone
# from authentication.models import CustomUser
# from reactions.models import Reaction


# class Notification(models.Model):
#     NOTIFICATION_TYPES = [
#         ('follow', 'Follow'),
#         ('reaction', 'Reaction'),
#     ]

#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')  # recipient
#     sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='actions')  # the user who performed the action
#     reactions = models.ForeignKey(Reaction, on_delete=models.CASCADE, related_name='reaction_notifications', null=True, blank=True)  # Ensure it's optional
#     notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
#     created_at = models.DateTimeField(default=timezone.now)
#     is_read = models.BooleanField(default=False)

#     def __str__(self):
#         if self.notification_type == 'follow':
#             return f"{self.sender.username} started following you"
#         elif self.notification_type == 'reaction':
#             return f"{self.sender.username} reacted to your post"
#         return f"Notification for {self.user.username}"

#     @classmethod
#     def unread_count_for_user(cls, user):
#         return cls.objects.filter(user=user, is_read=False).count()

# notifications/models.py

from django.db import models
from django.utils import timezone
from authentication.models import CustomUser
from reactions.models import Reaction  # Import Reaction model
from profile_app.models import Follow  # Import Follow model if needed

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('follow', 'Follow'),
        ('reaction', 'Reaction'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')  # recipient
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='actions')  # the user who performed the action
    reactions = models.ForeignKey(Reaction, on_delete=models.CASCADE, related_name='reaction_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        if self.notification_type == 'follow':
            return f"{self.sender.username} started following you"
        elif self.notification_type == 'reaction':
            return f"{self.sender.username} reacted to your post"
        return f"Notification for {self.user.username}"

    @classmethod
    def unread_count_for_user(cls, user):
        return cls.objects.filter(user=user, is_read=False).count()
