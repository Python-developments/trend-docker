import random
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.mail import send_mail
from .managers import CustomUserManager
from django.db.models.signals import post_delete
from django.dispatch import receiver


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    CustomUser model extends AbstractBaseUser and PermissionsMixin to provide 
    a customized user model with additional fields like phone_number, avatar, 
    and block_count, along with an OTP mechanism for password reset.
    """
    username = models.CharField(max_length=35, unique=True)
    first_name = models.CharField(max_length=35, blank=True, null=True)
    last_name = models.CharField(max_length=35, blank=True, null=True)
    bio = models.TextField(max_length=80, blank=True, null=True)
    phone_number = models.CharField(max_length=13, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    block_count = models.PositiveIntegerField(default=0)
    avatar = models.ImageField(upload_to='images/', default='images/avatar-default.png', blank=True, null=True)
    last_otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    created_data = models.DateTimeField(auto_now_add=True)
    updated_data = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        """
        Save Method
        The save method is overridden to incorporate password hashing using 
        Django's make_password function, ensuring hashing even in scenarios 
        where it could otherwise fail.
        """
        if self.password and not self.password.startswith('pbkdf2_sha256'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def generate_otp(self):
        self.last_otp = f'{random.randint(100000, 999999):06}'
        self.otp_expiry = timezone.now() + timedelta(minutes=10)
        self.save()

    def send_password_reset_email(self):
        mail_subject = 'Reset your password'
        message = f"""
        Hi {self.email},

        We received a request to reset your password. Your OTP code is:

        {self.last_otp}

        This code is valid for 10 minutes. If you didn't request a password reset, you can ignore this email.

        Thanks,
        Your team
        """
        send_mail(mail_subject, message, 'admin@mywebsite.com', [self.email])


class Block(models.Model):
    """
    Block model defines a relationship where one user (blocker) can block 
    another user (blocked). It enforces unique constraints to prevent duplicate 
    blocks and includes logic to automatically manage block_count and unfollow 
    relationships on block and unblock actions.
    """
    blocker = models.ForeignKey(CustomUser, related_name='blocking', on_delete=models.CASCADE)
    blocked = models.ForeignKey(CustomUser, related_name='blocked_by', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')  # ensures that a user cannot block the same user more than once
        indexes = [
            models.Index(fields=['blocker']),
            models.Index(fields=['blocked']),
        ]

    def save(self, *args, **kwargs):
        """
        Save method with block counter logic.
        Increments the block_count for the blocker when a block is created.
        """
        if not self.pk:  # Only increment on new blocks
            self.blocker.block_count += 1
            self.blocker.save()

        # Handle unfollow on block (if relevant)
        from profile_app.models import Follow
        Follow.objects.filter(follower=self.blocker, following=self.blocked).delete()
        Follow.objects.filter(follower=self.blocked, following=self.blocker).delete()

        super().save(*args, **kwargs)


# Automatically decrement block count when a block is removed
@receiver(post_delete, sender=Block)
def decrement_block_count(sender, instance, **kwargs):
    """
    Decrements the block_count for the blocker when a block is removed.
    """
    instance.blocker.block_count -= 1
    instance.blocker.save()
