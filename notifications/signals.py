# notifications/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Notification
from reactions.models import Reaction
from profile_app.models import Follow

@receiver(post_save, sender=Reaction)
def create_reaction_notification(sender, instance, created, **kwargs):
    if created:
        if not Notification.objects.filter(
            user=instance.post.user,
            sender=instance.user,
            notification_type='reaction',
            reactions=instance
        ).exists():
            Notification.objects.create(
                user=instance.post.user,
                sender=instance.user,
                notification_type='reaction',
                reactions=instance,
                created_at=timezone.now()
            )

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        if not Notification.objects.filter(
            user=instance.following,
            sender=instance.follower,
            notification_type='follow'
        ).exists():
            Notification.objects.create(
                user=instance.following,
                sender=instance.follower,
                notification_type='follow',
                created_at=timezone.now()
            )









# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.utils import timezone
# from .models import Notification
# from reactions.models import Reaction
# from profile_app.models import Follow  # Example follow model


# @receiver(post_save, sender=Reaction)
# def create_reaction_notification(sender, instance, created, **kwargs):
#     """
#     Signal to create a notification when a reaction is made on a post.
#     Triggered when a new Reaction instance is created.
#     """
#     if created:
#         # Check if a reaction notification already exists from this sender to the post author
#         if not Notification.objects.filter(
#             user=instance.post.user,
#             sender=instance.user,
#             notification_type='reaction',
#             reactions=instance
#         ).exists():
#             # Create the notification with the specific reaction type
#             Notification.objects.create(
#                 user=instance.post.user,       # recipient (the post author)
#                 sender=instance.user,          # the user who reacted
#                 notification_type='reaction',
#                 reactions=instance,            # link to the reaction
#                 created_at=timezone.now()
#             )



# @receiver(post_save, sender=Follow)
# def create_follow_notification(sender, instance, created, **kwargs):
#     """
#     Signal to create a notification when a follow action occurs.
#     Triggered when a new Follow instance is created.
#     """
#     if created:
#         # Check if a follow notification already exists from this follower to the following user
#         if not Notification.objects.filter(
#             user=instance.following,
#             sender=instance.follower,
#             notification_type='follow'
#         ).exists():
#             Notification.objects.create(
#                 user=instance.following,   # recipient (the user being followed)
#                 sender=instance.follower,  # the user who followed
#                 notification_type='follow',
#                 created_at=timezone.now()
#             )
