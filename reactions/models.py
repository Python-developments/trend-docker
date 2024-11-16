from django.db import models
from django.db.models import Count
from authentication.models import CustomUser


class Reaction(models.Model):
    REACTION_CHOICES = [
        ('love', 'Love'),
        ('like', ' Like'),
        ('haha', ' Haha'),
        ('wow', ' Wow'),
        ('crying', ' Crying'),
        ('angry', ' Angry'),
    ]

    post = models.ForeignKey('post.Post', on_delete=models.CASCADE, related_name='post_reactions')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_reaction_per_user_per_post')
        ]
    def __str__(self):
        return f"{self.user.username} reacted {self.get_reaction_type_display()} to post {self.post.id}"
    
    @classmethod
    def get_reaction_summary(cls, post):
        """
        Returns a summary of reactions for a specific post, including emojis.
        """
        reactions = cls.objects.filter(post=post).values('reaction_type').annotate(count=Count('reaction_type'))
        reaction_summary = [
            {
                "reaction_type": dict(cls.REACTION_CHOICES).get(reaction['reaction_type']),
                "count": reaction['count']
            }
            for reaction in reactions
        ]
        return reaction_summary

   