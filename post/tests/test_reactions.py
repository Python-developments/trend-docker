from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from post.models import Post, Reaction
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError


class ReactionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test users
        cls.user1 = User.objects.create_user(username='user1', password='pass')
        cls.user2 = User.objects.create_user(username='user2', password='pass')

        # Create test posts
        cls.post1 = Post.objects.create(user=cls.user1, content='Post 1 content')
        cls.post2 = Post.objects.create(user=cls.user2, content='Post 2 content')

        # Define reaction types
        cls.reaction_like = 'like'
        cls.reaction_love = 'love'
        cls.reaction_haha = 'haha'

    def test_create_reaction(self):
        """Test that a user can react to a post."""
        reaction = Reaction.objects.create(
            user=self.user1,
            post=self.post1,
            reaction_type=self.reaction_like
        )
        self.assertEqual(reaction.user, self.user1)
        self.assertEqual(reaction.post, self.post1)
        self.assertEqual(reaction.reaction_type, self.reaction_like)

    def test_user_can_only_react_once_per_post(self):
        """Test that a user cannot react to the same post more than once."""
        Reaction.objects.create(
            user=self.user1,
            post=self.post1,
            reaction_type=self.reaction_like
        )
        with self.assertRaises(IntegrityError):
            Reaction.objects.create(
                user=self.user1,
                post=self.post1,
                reaction_type=self.reaction_love
            )

    def test_user_can_change_reaction(self):
        """Test that a user can change their reaction to a post."""
        reaction = Reaction.objects.create(
            user=self.user1,
            post=self.post1,
            reaction_type=self.reaction_like
        )
        # Change the reaction type
        reaction.reaction_type = self.reaction_love
        reaction.save()
        updated_reaction = Reaction.objects.get(id=reaction.id)
        self.assertEqual(updated_reaction.reaction_type, self.reaction_love)

    def test_reaction_counts(self):
        """Test that reaction counts are accurate."""
        # User1 reacts to Post1
        Reaction.objects.create(user=self.user1, post=self.post1, reaction_type=self.reaction_like)
        # User2 reacts to Post1
        Reaction.objects.create(user=self.user2, post=self.post1, reaction_type=self.reaction_love)

        total_reactions = Reaction.objects.filter(post=self.post1).count()
        self.assertEqual(total_reactions, 2)

        like_count = Reaction.objects.filter(post=self.post1, reaction_type=self.reaction_like).count()
        self.assertEqual(like_count, 1)

        love_count = Reaction.objects.filter(post=self.post1, reaction_type=self.reaction_love).count()
        self.assertEqual(love_count, 1)

    def test_delete_reaction(self):
        """Test that a reaction can be deleted."""
        reaction = Reaction.objects.create(
            user=self.user1,
            post=self.post1,
            reaction_type=self.reaction_like
        )
        reaction_id = reaction.id
        reaction.delete()
        exists = Reaction.objects.filter(id=reaction_id).exists()
        self.assertFalse(exists)

    def test_invalid_reaction_type(self):
        """Test that invalid reaction types are rejected."""
        with self.assertRaises(ValidationError):
            reaction = Reaction(
                user=self.user1,
                post=self.post1,
                reaction_type='invalid_type'
            )
            reaction.full_clean()

    def test_react_to_nonexistent_post(self):
        """Test reacting to a post that doesn't exist."""
        with self.assertRaises(Post.DoesNotExist):
            Reaction.objects.create(
                user=self.user1,
                post=Post.objects.get(id=9999),  # Assuming this ID doesn't exist
                reaction_type=self.reaction_like
            )

    def test_unauthenticated_user_cannot_react(self):
        """Test that an unauthenticated user cannot react to a post."""
        # Log out the user if logged in
        self.client.logout()
        response = self.client.post(
            reverse('react_to_post', args=[self.post1.id]),
            {'reaction_type': self.reaction_like}
        )
        # Assuming unauthenticated users are redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/accounts/login/?next=/posts/{self.post1.id}/react/')
        reaction_exists = Reaction.objects.filter(user=self.user1, post=self.post1).exists()
        self.assertFalse(reaction_exists)

    def test_authenticated_user_can_react_via_view(self):
        """Test that an authenticated user can react to a post via the view."""
        self.client.login(username='user1', password='pass')
        response = self.client.post(
            reverse('react_to_post', args=[self.post1.id]),
            {'reaction_type': self.reaction_like}
        )
        self.assertEqual(response.status_code, 302)  # Assuming a redirect after success
        reaction_exists = Reaction.objects.filter(user=self.user1, post=self.post1).exists()
        self.assertTrue(reaction_exists)

    def test_unique_reaction_per_user_per_post(self):
        """Test that the database enforces unique reactions per user per post."""
        Reaction.objects.create(
            user=self.user1,
            post=self.post1,
            reaction_type=self.reaction_like
        )
        with self.assertRaises(IntegrityError):
            Reaction.objects.create(
                user=self.user1,
                post=self.post1,
                reaction_type=self.reaction_like
            )

    def test_reaction_string_representation(self):
        """Test the string representation of a Reaction."""
        reaction = Reaction.objects.create(
            user=self.user1,
            post=self.post1,
            reaction_type=self.reaction_haha
        )
        expected_string = f"{self.user1.username} reacted {self.reaction_haha} to Post {self.post1.id}"
        self.assertEqual(str(reaction), expected_string)
