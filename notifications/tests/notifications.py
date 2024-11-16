from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from reactions.models import Reaction
from profile_app.models import Follow
from .models import Notification

User = get_user_model()

class NotificationSignalTest(TestCase):
    def setUp(self):
        # Create two users for testing
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')

    def test_reaction_notification_created(self):
        # Assuming a post by user1 exists in the system
        post = Post.objects.create(author=self.user1, content='Test post')

        # User2 reacts to user1's post
        reaction = Reaction.objects.create(user=self.user2, post=post, type='like')

        # Check if a notification was created for user1
        notification = Notification.objects.filter(user=self.user1, sender=self.user2, notification_type='reaction')
        self.assertTrue(notification.exists())
        self.assertEqual(notification.count(), 1)
        self.assertEqual(notification.first().reactions, reaction)

    def test_follow_notification_created(self):
        # User2 follows user1
        follow = Follow.objects.create(follower=self.user2, following=self.user1)

        # Check if a notification was created for user1
        notification = Notification.objects.filter(user=self.user1, sender=self.user2, notification_type='follow')
        self.assertTrue(notification.exists())
        self.assertEqual(notification.count(), 1)
