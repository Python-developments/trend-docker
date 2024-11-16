from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

@receiver(post_save, sender='post.Reaction')
def create_reaction_notification(sender, instance, created, **kwargs):
    if created:
        Notification = apps.get_model('notifications', 'Notification')
        Notification.objects.create(
            user=instance.post.user,
            sender=instance.user,
            notification_type='reaction',
            reactions=instance,
        )
