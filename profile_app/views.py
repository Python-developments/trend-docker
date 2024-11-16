from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef
from django.views.decorators.csrf import csrf_exempt

from .models import Profile, Follow
from .serializers import ProfileSerializer, FollowSerializer, ProfileUpdateSerializer
from authentication.models import Block, CustomUser
from authentication.pagination import CustomPageNumberPagination

# --------------------------------------
# Helper Functions
# --------------------------------------

def get_filtered_user_profiles(user_ids, request_user):
    """
    Helper function to filter user profiles based on mutual blocked relationships.
    """
    blocked_users = Block.objects.filter(blocker=request_user).values_list('blocked', flat=True)
    blocked_by_users = Block.objects.filter(blocked=request_user).values_list('blocker', flat=True)
    all_blocked_users = set(blocked_users).union(set(blocked_by_users))
    filtered_user_ids = [user_id for user_id in user_ids if user_id not in all_blocked_users]
    return Profile.objects.filter(user__in=filtered_user_ids).order_by('-created_at')

# --------------------------------------
# Profile-Related Views
# --------------------------------------

class ProfileViewList(generics.ListAPIView):
    """
    API View to list all profiles. Profile creation is not allowed here since
    profiles are automatically created when a user registers.
    """
    serializer_class = ProfileSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """
        Filter out profiles of users who are blocked by or have blocked the current user.
        """
        queryset = Profile.objects.all().order_by('-created_at')
        user = self.request.user
        if user.is_authenticated:
            blocked_users = Block.objects.filter(blocker=user).values_list('blocked', flat=True)
            blocked_by_users = Block.objects.filter(blocked=user).values_list('blocker', flat=True)
            users_to_exclude = set(blocked_users).union(set(blocked_by_users))
            queryset = queryset.exclude(user__in=users_to_exclude)
        return queryset


class ProfileDetails(generics.RetrieveUpdateAPIView):
    """
    API View to retrieve or update a profile instance. Deletion is not allowed.
    Only the owner of a profile can update it.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Exclude profiles of users who have blocked the current user.
        """
        queryset = Profile.objects.all()
        user = self.request.user
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


class ProfileUpdateView(generics.UpdateAPIView):
    """
    API View to allow a user to update their own profile. Only the owner of a profile can update it.
    """
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

# --------------------------------------
# Follow-Related Views
# --------------------------------------

class FollowUserView(generics.CreateAPIView):
    """
    View to allow a user to follow another user.
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
    API View to allow a user to unfollow another user.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        follower = request.user
        following = get_object_or_404(CustomUser, pk=self.kwargs.get('pk'))

        follow = Follow.objects.filter(follower=follower, following=following)
        if not follow.exists():
            return Response({'error': 'You are not following this user.'}, status=status.HTTP_400_BAD_REQUEST)

        follow.first().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowersListAPIView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        request_user = self.request.user
        try:
            user = CustomUser.objects.get(pk=user_id)
            followers = user.followers.all().values_list('follower', flat=True)
            return get_filtered_user_profiles(followers, request_user)
        except CustomUser.DoesNotExist:
            return Profile.objects.none()


class FollowingListAPIView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        request_user = self.request.user
        try:
            user = CustomUser.objects.get(pk=user_id)
            followings = user.following.all().values_list('following', flat=True)
            return get_filtered_user_profiles(followings, request_user)
        except CustomUser.DoesNotExist:
            return Profile.objects.none()

# --------------------------------------
# Support Views
# --------------------------------------

@csrf_exempt
def support(request):
    """
    View for submitting a support request. (Basic form handling)
    """
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        # Optionally, send email to support team (uncomment for actual use)
        """
        send_mail(
            subject=f"Support Request from {name}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["support@yourwebsite.com"],
            fail_silently=False,
        )
        """
        # Redirect to a success page
        return redirect("support_success")
    return render(request, "support.html")


def support_success(request):
    """
    View for support success confirmation.
    """
    return render(request, "support_success.html")
