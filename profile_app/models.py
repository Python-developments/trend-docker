import os
from django.db import models
from authentication.models import CustomUser
from django.db.models.signals import post_save
from reactions.models import Reaction
from django.dispatch import receiver
from django.core.exceptions import ValidationError


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile', null=True)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    hide_avatar = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    location = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.avatar and self.user and self.user.avatar and self.user.avatar.name != 'images/avatar.jpeg':
            self.avatar = self.user.avatar
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

    def post_count(self):
        return self.user.posts.count()

    def follow_count(self):
        return self.user.following.count()

    def follower_count(self):
        return self.user.followers.count()

    def total_reactions(self):
        return Reaction.objects.filter(post__user=self.user).count()


class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, related_name='following', on_delete=models.CASCADE, null=True)
    following = models.ForeignKey(CustomUser, related_name='followers', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ('follower', 'following')  # Ensure a unique follow relationship

    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'

    def clean(self):
        if Follow.objects.filter(following=self.following, follower=self.follower).exists():
            raise ValidationError('You are already following this user.')


@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        if instance.avatar and instance.avatar.name != 'images/avatar.jpeg':  # Check if a custom avatar is provided
            profile.avatar = instance.avatar
            profile.save()


@receiver(post_save, sender=Profile)
def update_user_from_profile(sender, instance, created, **kwargs):
    if not created:  # Skip for new profiles
        if instance.user and instance.user.avatar != instance.avatar:
            instance.user.avatar = instance.avatar
            instance.user.save()
