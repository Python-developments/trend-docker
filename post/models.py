from django.db import models
from django.db.models import Count, Min
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

    def add_or_update_reaction(self, user, reaction_type):
        """
        Add, update, or remove a reaction for this post based on user input.
        If 'reaction_type' is 'remove', it explicitly removes the reaction.
        """
        # Check if the user already reacted to this post
        existing_reaction = Reaction.objects.filter(post=self, user=user).first()

        if reaction_type == "remove":
            if existing_reaction:
                existing_reaction.delete()
                action = "removed"
            else:
                action = "none"  # No action taken because no reaction exists
            reaction_type = None  # No active reaction after removal
        else:
            if existing_reaction:
                if existing_reaction.reaction_type == reaction_type:
                    # If the same reaction is clicked, return the current state (no-op)
                    action = "no_change"
                else:
                    # Update the reaction if the type is different
                    existing_reaction.reaction_type = reaction_type
                    existing_reaction.save()
                    action = "updated"
            else:
                # Add a new reaction if none exists
                Reaction.objects.create(post=self, user=user, reaction_type=reaction_type)
                action = "added"

        # Build the response object with post data
        return {
            "id": self.id,
            "custom_user_id": self.user.id,
            "profile_id": self.profile.id if self.profile else None,
            "username": self.user.username,
            "avatar": self.user.avatar.url if self.user.avatar else None,
            "image": self.image.url if self.image else None,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "like_counter": self.like_count(),
            "comment_counter": self.comment_count(),
            "liked": self.likes.filter(user=user).exists(),
            "user_reaction": reaction_type,  # Will be None if reaction was removed
            "total_reaction_count": self.post_reactions.count(),
            "reactions_list": [
                {"user": reaction.user.username, "reaction_type": reaction.reaction_type}
                for reaction in self.post_reactions.select_related("user").all()
            ],
            "reaction_list_count": list(
                self.post_reactions.values("reaction_type").annotate(count=Count("reaction_type")).order_by("-count")
            ),
             "top_3_reactions": [
                    {
                        "reaction_type": reaction["reaction_type"],
                        "count": reaction["count"],
                        "created_at": reaction["earliest_reaction"],
                    }
                    for reaction in self.post_reactions.values("reaction_type")
                    .annotate(count=Count("reaction_type"), earliest_reaction=Min("created_at"))
                    .order_by("-count")[:3]
                ],  # Top 3 reactions by count    
            "action": action,  # 'added', 'updated', 'removed', or 'no_change'
        }




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
