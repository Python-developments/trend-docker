# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.utils import timezone
# from django.apps import apps

# @receiver(post_save, sender='profile_app.Follow')
# def create_follow_notification(sender, instance, created, **kwargs):
#     if created:
#         Notification = apps.get_model('notifications', 'Notification')
#         Notification.objects.create(
#             user=instance.following,
#             sender=instance.follower,
#             notification_type='follow',
#             created_at=timezone.now(),
#         )
