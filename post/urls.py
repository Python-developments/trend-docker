from django.urls import path

from .views import (
    PostList, PostDetail,
    CommentDetail,
    PostComments, CreatePost, CreateComment,  HideOrUnhidePostView,
    ReactionToggleView,ReactionListView)


urlpatterns = [
    # posts endpoints
    path('createpost/', CreatePost.as_view(), name='create_post'),
    path('posts-list/', PostList.as_view(), name='post-list'),
    path('<int:pk>/', PostDetail.as_view(), name='post-detail'),

    # comments endpoints
    path('createcomment/', CreateComment.as_view(), name='create_comment'),
    path('<int:pk>/comments/', PostComments.as_view(), name='post_comments'),
    path('comment/<int:pk>/', CommentDetail.as_view(), name='comment-detail'),

    path('hide-or-unhide-post/', HideOrUnhidePostView.as_view(), name='hide-or-unhide-post'),

    path('<int:pk>/toggle-reaction', ReactionToggleView.as_view(), name='toggle-reaction'),
    path('<int:pk>/reactions-list',  ReactionListView.as_view(), name='reactions-list'),
    # In home/urls.py
]