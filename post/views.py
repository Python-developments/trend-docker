from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Post, Comment, LikePost, LikeCounter, HiddenPost, CommentCounter
from reactions.models import Reaction
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from authentication.pagination import CustomPageNumberPagination
from .serializers import (CreateCommentSerializer,
                          CreatePostSerializer,
                          PostSerializer,
                          CommentSerializer,
                          LikeToggleSerializer,
                          HiddenPostSerializer,
                          ReactionSerializer,
                          PostReactionToggleSerializer)
from rest_framework.permissions import IsAuthenticated
from authentication.models import Block, CustomUser


# Create Post view
class CreatePost(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = CreatePostSerializer
    permission_classes = [IsAuthenticated]

    # need adjustment: Overriding `perform_create` may not be necessary if user assignment is handled in the serializer's `create` method.
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # need adjustment: Overriding the `create` method is unnecessary unless you need custom response data.
    # If you need additional fields in the response, consider including them in the serializer.
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance

        # need adjustment: Accessing `instance.image.url` can raise an error if `image` is None.
        # Adjust to handle cases where `image` might not be provided.
        response_data = {
            "id": instance.id,
            "image": instance.image.url if instance.image else None,  # Adjusted to handle None case.
            "content": instance.content,
            "username": instance.user.username,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)





# Post views
class PostList(generics.ListAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        '''
        Restrict the user from viewing posts if blocked. This means the posts will not be available for liking or commenting, effectively preventing a blocked user from liking or commenting

        The implementation also allows users to hide their own posts, but still be able to access
        those hidden posts themselves. However, other users will not be able to access posts
        that are hidden by other users.
        '''
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            blocked_users = Block.objects.filter(blocker=user).values_list('blocked', flat=True)
            blocked_by_users = Block.objects.filter(blocked=user).values_list('blocker', flat=True)
            users_to_exclude = list(set(blocked_users).union(set(blocked_by_users)))
            # Retrieve IDs of posts hidden by any user
            # hidden_post_ids = HiddenPost.objects.values_list('post_id', flat=True)
            hidden_post_ids = HiddenPost.objects.filter(user=user).values_list('post_id', flat=True)
            queryset = Post.objects.exclude(user__in=users_to_exclude).exclude(id__in=hidden_post_ids)

        return queryset.order_by('-created_at')


class PostDetail(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        """
        Pass additional context like the request to the serializer.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


    def perform_update(self, serializer):
        """
        Save the post with the authenticated user as the owner.
        """
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        """
        Ensure only the post owner can delete the post.
        """
        if instance.user == self.request.user:
            instance.delete()
        else:
            raise PermissionDenied("You do not have permission to delete this post.")





# Create Comment view
class CreateComment(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CreateCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Save the new comment and set the user automatically
        comment = serializer.save(user=self.request.user)
        
        # Update CommentCounter
        post = comment.post  # Get the post from the newly created comment
        comment_counter, created = CommentCounter.objects.get_or_create(post=post)
        comment_counter.count = post.comment_count()
        comment_counter.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)  # Call perform_create to handle saving and updating
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)





# Comment views
# class CommentList(generics.ListCreateAPIView):
#     queryset = Comment.objects.all()
#     serializer_class = CommentSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CreateCommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        # Only the owner of the comment can update it
        comment = self.get_object()
        if comment.user != self.request.user:
            raise PermissionDenied("You can only update your own comment.")
        serializer.save()

    def perform_destroy(self, instance):
        # Only the owner of the comment can delete it
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own comment.")
        instance.delete()


# Post comments view
class PostComments(generics.ListAPIView):
    serializer_class = CommentSerializer
    pagination_class = CustomPageNumberPagination


    def get_queryset(self):
        post_id = self.kwargs['pk']  # Get the post ID from the URL parameter
        request_user = self.request.user
        post = get_object_or_404(Post, pk=post_id)  # Retrieve the post object

        if not request_user.is_authenticated:
            # Handle case when user is not authenticated
            return Comment.objects.none()
        # Get list of blocked user IDs
        blocked_users = Block.objects.filter(blocker=request_user).values_list('blocked', flat=True)
        blocked_by_users = Block.objects.filter(blocked=request_user).values_list('blocker', flat=True)
        users_to_exclude = list(set(blocked_users).union(set(blocked_by_users)))

        # Exclude comments from blocked users
        return Comment.objects.filter(post=post).exclude(user__in=users_to_exclude).order_by('-created_at')


        
class HideOrUnhidePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        post_id = request.data.get('post_id')
        user = request.user

        if not post_id:
            return Response({"detail": "post_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            HiddenPost.objects.get(user=user, post=post)
            return Response({"detail": "Post is already hidden."}, status=status.HTTP_400_BAD_REQUEST)
        except HiddenPost.DoesNotExist:
            HiddenPost.objects.create(user=user, post=post)
            return Response({"detail": "Post hidden successfully."}, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        post_id = request.data.get('post_id')
        user = request.user

        if not post_id:
            return Response({"detail": "post_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            hidden_post = HiddenPost.objects.get(user=user, post=post)
            hidden_post.delete()
            return Response({"detail": "Post unhidden successfully."}, status=status.HTTP_200_OK)
        except HiddenPost.DoesNotExist:
            return Response({"detail": "Post is not hidden."}, status=status.HTTP_400_BAD_REQUEST)

class ReactionToggleView(generics.CreateAPIView):
    serializer_class = PostReactionToggleSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        """
        Pass additional context to the serializer, including the post instance.
        """
        context = super().get_serializer_context()
        post_id = self.kwargs.get('pk')  # Get the post ID from the URL
        post = get_object_or_404(Post, pk=post_id)  # Retrieve the post instance
        context['post'] = post  # Add the post instance to the context
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_201_CREATED)



class ReactionListView(generics.ListAPIView):
    serializer_class = ReactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs.get('pk')
        return Reaction.objects.filter(post_id=post_id)