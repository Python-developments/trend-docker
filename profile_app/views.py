from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef
from .models import Profile, Follow
from .serializers import ProfileSerializer, FollowSerializer
from authentication.models import Block, CustomUser
from authentication.pagination import CustomPageNumberPagination

# --------------------------------------
# Profile-Related Views
# --------------------------------------

class ProfileListView(generics.ListAPIView):
    """
    API View to list all profiles.
    Profile creation is not allowed here as profiles are auto-created during user registration.
    """
    serializer_class = ProfileSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter out profiles of users who are blocked by or have blocked the current user.
        """
        user = self.request.user
        queryset = Profile.objects.all().order_by('-created_at')
        if user.is_authenticated:
            blocked_users = Block.objects.filter(blocker=user).values_list('blocked', flat=True)
            blocked_by_users = Block.objects.filter(blocked=user).values_list('blocker', flat=True)
            users_to_exclude = set(blocked_users).union(set(blocked_by_users))
            queryset = queryset.exclude(user__in=users_to_exclude)
        return queryset


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    API View to retrieve or update a profile instance.
    Deletion is not allowed. Only the owner of a profile can update it.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Exclude profiles of users who have blocked the current user.
        """
        user = self.request.user
        queryset = Profile.objects.all()
        if user.is_authenticated:
            blocked_subquery = Block.objects.filter(blocker=OuterRef('user'), blocked=user)
            queryset = queryset.annotate(is_blocked=Exists(blocked_subquery)).exclude(is_blocked=True)
        return queryset

    def update(self, request, *args, **kwargs):
        """
        Allow profile updates only if the requester is the owner of the profile.
        """
        profile = self.get_object()
        if request.user != profile.user:
            raise PermissionDenied("You do not have permission to update this profile.")
        return super().update(request, *args, **kwargs)

# --------------------------------------
# Follow-Related Views
# --------------------------------------

class FollowUserView(generics.CreateAPIView):
    """
    API View to follow a user.
    """
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        follower = request.user
        following_id = request.data.get('following_id')

        if not following_id:
            return Response({'error': 'Following user ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if follower.id == int(following_id):
            return Response({'error': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        following = get_object_or_404(CustomUser, pk=following_id)

        if Follow.objects.filter(follower=follower, following=following).exists():
            return Response({'error': 'You are already following this user.'}, status=status.HTTP_400_BAD_REQUEST)

        follow = Follow.objects.create(follower=follower, following=following)
        serializer = self.get_serializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UnfollowUserView(generics.DestroyAPIView):
    """
    API View to unfollow a user.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        follower = request.user
        following = get_object_or_404(CustomUser, pk=self.kwargs.get('pk'))

        if follower == following:
            return Response({'error': 'You cannot unfollow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        follow = Follow.objects.filter(follower=follower, following=following)
        if not follow.exists():
            return Response({'error': 'You are not following this user.'}, status=status.HTTP_400_BAD_REQUEST)

        follow.first().delete()
        return Response({'success': f'You have successfully unfollowed {following.username}.'}, status=status.HTTP_200_OK)


class FollowersListView(generics.ListAPIView):
    """
    API View to list followers of a user.
    """
    serializer_class = ProfileSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        user = get_object_or_404(CustomUser, pk=user_id)
        follower_ids = user.followers.all().values_list('follower', flat=True)
        return Profile.objects.filter(user__in=follower_ids)


class FollowingListView(generics.ListAPIView):
    """
    API View to list users followed by a user.
    """
    serializer_class = ProfileSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        user = get_object_or_404(CustomUser, pk=user_id)
        following_ids = user.following.all().values_list('following', flat=True)
        return Profile.objects.filter(user__in=following_ids)


# View for the 'support.html' page
def support(request):
    return render(request, 'support.html')

# View for the 'support_success.html' page
def support_success(request):
    return render(request, 'support_success.html')