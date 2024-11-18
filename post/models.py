from django.db import models
from django.db.models import Count
from authentication.models import CustomUser
from profile_app.models import Profile
from reactions.models import Reaction



class Post(models.Model):
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='posts')
    profile = models.ForeignKey('profile_app.Profile', on_delete=models.CASCADE, related_name='posts', null=True)
    image = models.ImageField(upload_to='images/', blank=False, null=False)
    content = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.content[:20]}" if self.content else "No Content"

    def add_or_update_reaction(self, user, reaction_type):
        """
        Add, update, or remove a reaction for this post based on user input.
        """
        # Debugging: Log the inputs
        print(f"add_or_update_reaction called with reaction_type={reaction_type}, user={user.username}")

        # Check if the user already reacted to this post
        existing_reaction = Reaction.objects.filter(post=self, user=user).first()

        # Debugging: Log existing reaction
        print(f"Existing reaction: {existing_reaction}")

        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # If the user clicks the same reaction twice, remove it
                existing_reaction.delete()
                action = "removed"
                reaction_type = None  # No active reaction after removal
            else:
                # Update the reaction if the type is different
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                action = "updated"
        else:
            # Add a new reaction if none exists
            Reaction.objects.create(post=self, user=user, reaction_type=reaction_type)
            action = "added"


        # Debugging: Log the result of the operation
        print(f"Action taken: {action}")

        # Build the response object
        return {
            "id": self.id,
            "action": action,
            "user_reaction": reaction_type,
            "total_reaction_count": self.post_reactions.count(),
        }

        # # Build the response object with post data
        # return {
        #     "id": self.id,
        #     "custom_user_id": self.user.id,
        #     "profile_id": self.profile.id if self.profile else None,
        #     "username": self.user.username,
        #     "avatar": self.user.avatar.url if self.user.avatar else None,
        #     "image": self.image.url if self.image else None,
        #     "content": self.content,
        #     "created_at": self.created_at,
        #     "updated_at": self.updated_at,
        #     "like_counter": self.like_count(),
        #     "comment_counter": self.comment_count(),
        #     "liked": self.likes.filter(user=user).exists(),
        #     "user_reaction": reaction_type,  # Will be None if reaction was removed
        #     "total_reaction_count": self.post_reactions.count(),
        #     "reactions_list": [
        #         {"user": reaction.user.username, "reaction_type": reaction.reaction_type}
        #         for reaction in self.post_reactions.select_related("user").all()
        #     ],
        #     "reaction_list_count": list(
        #         self.post_reactions.values("reaction_type").annotate(count=Count("reaction_type")).order_by("-count")
        #     ),
        #     "top_3_reactions": [
        #         {
        #             "reaction_type": reaction["reaction_type"],
        #             "count": reaction["count"],
        #             "user": self.post_reactions.filter(reaction_type=reaction["reaction_type"]).first().user.username,
        #         }
        #         for reaction in self.post_reactions.values("reaction_type")
        #         .annotate(count=Count("reaction_type"))
        #         .order_by("-count")[:3]
        #     ],
        #     "action": action,  # Add, update, remove, or no_change
        # }



    def get_top_reactions(self, top_n=3):
        """
        Returns the top N reactions for the post, including reaction_type, a single user, and count for each reaction type.
        """
        reaction_groups = (
            self.post_reactions.values('reaction_type')  # Group by reaction type
            .annotate(count=Count('reaction_type'))  # Count occurrences for sorting
            .order_by('-count')[:top_n]  # Order by count and limit to top_n
        )

        top_reactions = []
        for reaction_group in reaction_groups:
            reaction_type = reaction_group["reaction_type"]
            count = reaction_group["count"]  # Get the count for this reaction type
            user = (
                self.post_reactions.filter(reaction_type=reaction_type)
                .select_related('user')  # Optimize query for user
                .values_list('user__username', flat=True)
                .first()  # Get the first username
            )
            top_reactions.append({
                "reaction_type": reaction_type,
                "count": count,  # Include the count
                "user": user  # Single user instead of a list
            })

        return top_reactions


    def reaction_list(self):
        """
        Retrieves a list of users and their reactions to the post.
        """
        reaction_icons = dict(Reaction.REACTION_CHOICES)

        # Ensure `post_id` is included in the query
        reactions = self.post_reactions.select_related('user').values(
            'user__username', 'reaction_type', 'post', 'post__content'
        )

        return [
            {
                "user": reaction['user__username'],
                "reaction_type": reaction_icons.get(reaction['reaction_type'], reaction['reaction_type']),
                "post": {
                    "id": reaction['post'],  # Use `post` instead of `post_id`
                    "content": reaction['post__content'],
                }
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
