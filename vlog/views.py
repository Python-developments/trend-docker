from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from .models import (
    Video, 
    VlogComment, 
    VlogLike,
    VlogReaction
)
from .serializers import (
    VideoSerializer, 
    VlogCommentSerializer,
    VlogLikeSerializer,
    VlogReactionSerializer
)

class VideoList(generics.ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        try:
            serializer.save(
                author=self.request.user
            )
            
        except ValidationError as ve:
            raise ValidationError(
                {'detail': ve.messages}
            )


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except ValidationError as ve:
            return Response(
                {'detail': ve.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class VideoDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != serializer.instance.author:
            raise ValidationError("You don't have permission to edit this video.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.author:
            raise ValidationError("You don't have permission to delete this video.")
        instance.delete()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_update(serializer)
        except ValidationError as ve:
            return Response({'detail': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ValidationError as ve:
            return Response({'detail': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

class CommentList(generics.ListCreateAPIView):
    serializer_class = VlogCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        video = get_object_or_404(Video, pk=self.kwargs['video_pk'])
        return VlogComment.objects.filter(video=video)

    def perform_create(self, serializer):
        video = get_object_or_404(Video, pk=self.kwargs['video_pk'])
        serializer.save(user=self.request.user, video=video)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except ValidationError as ve:
            return Response({'detail': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = VlogComment.objects.all()
    serializer_class = VlogCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != serializer.instance.user:
            raise ValidationError("You don't have permission to edit this comment.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.user:
            raise ValidationError("You don't have permission to delete this comment.")
        instance.delete()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_update(serializer)
        except ValidationError as ve:
            return Response({'detail': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ValidationError as ve:
            return Response({'detail': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

class LikeVideo(generics.CreateAPIView, generics.DestroyAPIView):
    serializer_class = VlogLikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VlogLike.objects.filter(user=self.request.user, video__pk=self.kwargs['video_pk'])

    def perform_create(self, serializer):
        video = get_object_or_404(Video, pk=self.kwargs['video_pk'])
        if VlogLike.objects.filter(user=self.request.user, video=video).exists():
            raise ValidationError("You have already liked this video.")
        serializer.save(user=self.request.user, video=video)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except ValidationError as ve:
            return Response({'detail': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def delete(self, request, *args, **kwargs):
        video = get_object_or_404(Video, pk=self.kwargs['video_pk'])
        like = get_object_or_404(VlogLike, user=self.request.user, video=video)
        like.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class VlogReactionToggleView(generics.CreateAPIView):
    serializer_class = VlogReactionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        video_id = self.kwargs.get('pk')
        try:
            video = Video.objects.get(pk=video_id)
        except Video.DoesNotExist:
            return Response({'detail': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            reaction = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            if str(e) == "Reaction removed.":
                return Response({'detail': 'Reaction removed.'}, status=status.HTTP_204_NO_CONTENT)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

class VlogReactionListView(generics.ListAPIView):
    serializer_class = VlogReactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        video_id = self.kwargs.get('pk')
        return VlogReaction.objects.filter(video_id=video_id)        