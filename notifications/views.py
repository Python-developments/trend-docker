from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db import models
from .models import Notification, Reaction, CustomUser
from .serializers import NotificationSerializer, UserSerializer
from profile_app.models import Follow


class NotificationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationListView(generics.ListAPIView):
    """
    Lists notifications for the authenticated user.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        """
        Returns notifications for the logged-in user, ordered by creation date.
        """
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        Customizes the list response to include total and unread notification counts.
        """
        queryset = self.get_queryset()
        counts = queryset.aggregate(
            total_count=models.Count('id'),
            unread_count=models.Count('id', filter=models.Q(is_read=False))
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response({
            "total_count": counts['total_count'],
            "unread_count": counts['unread_count'],
            "notifications": serializer.data
        })


class UsersWhoReactedToMyPostsView(generics.ListAPIView):
    """
    Lists users who reacted to the authenticated user's posts.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves users who reacted to the logged-in user's posts, excluding reactions by the user themselves.
        """
        user_posts = self.request.user.posts.all()  # Assuming `posts` is a related name for user's posts
        reactions = Reaction.objects.filter(post__in=user_posts).exclude(user=self.request.user).select_related('user')
        user_ids = reactions.values_list('user_id', flat=True).distinct()
        return CustomUser.objects.filter(id__in=user_ids)


class UsersWhoFollowMeView(generics.ListAPIView):
    """
    Lists users who follow the authenticated user.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves users following the logged-in user.
        """
        followers = Follow.objects.filter(following=self.request.user).select_related('follower')
        follower_ids = followers.values_list('follower_id', flat=True).distinct()
        return CustomUser.objects.filter(id__in=follower_ids)


# Optional: Add self-like prevention at the Notification creation level if needed.
def prevent_self_like(sender, instance, **kwargs):
    """
    Signal to prevent notifications for self-likes when a Reaction is created.
    """
    if instance.user == instance.reacted_by:  # Adjust field names as necessary
        return  # Skip creating a notification
    Notification.objects.create(
        user=instance.user,
        sender=instance.reacted_by,
        notification_type='reaction'
    )
