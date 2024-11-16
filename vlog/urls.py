from django.urls import path
from . import views

urlpatterns = [
    path('videos/', views.VideoList.as_view(), name='video-list'),
    path('videos/<int:pk>/', views.VideoDetail.as_view(), name='video-detail'),
    path('videos/<int:video_pk>/comments/', views.CommentList.as_view(), name='comment-list'),
    path('videos/<int:video_pk>/comments/<int:pk>/', views.CommentDetail.as_view(), name='comment-detail'),
    path('videos/<int:video_pk>/like/', views.LikeVideo.as_view(), name='like-video'),
    path('video/<int:pk>/reactions-toggle/',views.VlogReactionToggleView.as_view(), name='vlog-reaction-toggle'),
    path('video/<int:pk>/reactions-list/', views.VlogReactionListView.as_view(), name='vlog-reaction-list'),
]