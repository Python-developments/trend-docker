# notifications/urls.py

from django.urls import path
from .views import (
    NotificationListView,
    UsersWhoReactedToMyPostsView,
    UsersWhoFollowMeView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('users-who-reacted/', UsersWhoReactedToMyPostsView.as_view(), name='users-who-reacted'),
    path('users-who-follow/', UsersWhoFollowMeView.as_view(), name='users-who-follow'),
]
