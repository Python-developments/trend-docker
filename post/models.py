from django.db import models
from django.db.models import Count
from authentication.models import CustomUser
from profile_app.models import Profile
from reactions.models import Reaction



class Post(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts', null=True)
    image = models.ImageField(upload_to='images/', blank=False, null=False)
    content = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.content[:20]}" if self.content else "No Content"

    def like_count(self):
        """
        Returns the total number of likes on the post.
        """
        return self.likes.count()

    def comment_count(self):
        """
        Returns the total number of comments on the post.
        """
        return self.comments.count()

    def toggle_reaction(self, user, reaction_type):
        """
        Toggles a reaction for this post by the given user.
        If the reaction of the same type exists, it removes it.
        If a different reaction exists, it updates it.
        Otherwise, it adds the reaction.
        """
        existing_reaction = Reaction.objects.filter(post=self, user=user).first()

        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                existing_reaction.delete()  # Remove the reaction (toggle off)
                return {"action": "removed", "reaction_type": reaction_type}
            else:
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()  # Update the reaction type
                return {"action": "updated", "reaction_type": reaction_type}
        else:
            Reaction.objects.create(post=self, user=user, reaction_type=reaction_type)  # Add new reaction
            return {"action": "added", "reaction_type": reaction_type}

    def get_top_reactions(self, top_n=3):
        """
        Returns the top N reactions for the post.
        """
        reaction_counts = self.post_reactions.values('reaction_type').annotate(
            count=Count('reaction_type')
        ).order_by('-count')[:top_n]

        return [
            {"reaction_type": r["reaction_type"], "count": r["count"]}
            for r in reaction_counts
        ]

    def reaction_list(self):
        """
        Retrieves a list of users and their reactions to the post.
        """
        reaction_icons = dict(Reaction.REACTION_CHOICES)
        reactions = self.post_reactions.select_related('user').values('user__username', 'reaction_type')

        return [
            {
                "user": reaction['user__username'],
                "reaction_type": reaction_icons.get(reaction['reaction_type'], reaction['reaction_type'])
            }
            for reaction in reactions
        ]

    def reaction_list_count(self):
        """
        Retrieves the count of each reaction type.
        """
        reactions = self.post_reactions.values('reaction_type').annotate(count=Count('reaction_type'))
        return [
            {
                "reaction_type": dict(Reaction.REACTION_CHOICES).get(reaction['reaction_type'], reaction['reaction_type']),
                "count": reaction['count']
            }
            for reaction in reactions
        ]

    def total_reaction_count(self):
        """
        Returns the total count of all reactions on this post.
        """
        return self.post_reactions.count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username}: {self.content[:20]}..."


class LikePost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} liked post {self.post.id}"

    @classmethod
    def toggle_like(cls, post, user):
        """
        Toggles the like for a post by the user.
        """
        try:
            like = cls.objects.get(post=post, user=user)
            like.delete()
            return False  # Like removed
        except cls.DoesNotExist:
            cls.objects.create(post=post, user=user)
            return True  # Like added


class LikeCounter(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)


class CommentCounter(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)


class HiddenPost(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='hidden_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='hidden_by')

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} hidden post {self.post.id}"