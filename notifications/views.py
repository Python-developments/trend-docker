from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Notification, Reaction, CustomUser
from django.db import models
from .serializers import NotificationSerializer, UserSerializer
from profile_app.models import Follow



class NotificationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
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
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Use the correct related name to get user's posts
        user_posts = self.request.user.posts.all()
        # Get reactions to those posts
        reactions = Reaction.objects.filter(post__in=user_posts).select_related('user')
        # Get unique user IDs
        user_ids = reactions.values_list('user_id', flat=True).distinct()
        # Return users who reacted
        return CustomUser.objects.filter(id__in=user_ids)
    

class UsersWhoFollowMeView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        followers = Follow.objects.filter(following=self.request.user).select_related('follower')
        follower_ids = followers.values_list('follower_id', flat=True).distinct()
        return CustomUser.objects.filter(id__in=follower_ids)
