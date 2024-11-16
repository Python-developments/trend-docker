# # notifications/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.utils import timezone
# from notifications.models import Notification
# from reactions.models import Reaction  # Ensure Reaction is imported
# from profile_app.models import Follow  # Import Follow model or update as needed

# @receiver(post_save, sender=Reaction)
# def create_reaction_notification(sender, instance, created, **kwargs):
#     if created:
#         Notification.objects.create(
#             user=instance.post.user,
#             sender=instance.user,
#             notification_type='reaction',
#             reactions=instance,
#             created_at=timezone.now()
#         )

# @receiver(post_save, sender=Follow)
# def create_follow_notification(sender, instance, created, **kwargs):
#     if created:
#         Notification.objects.create(
#             user=instance.followed_user,
#             sender=instance.follower,
#             notification_type='follow',
#             created_at=timezone.now()
#         )
