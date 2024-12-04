from django.urls import path
from .views import (
    ProfileListView,
    ProfileDetailView,
    FollowUserView,
    UnfollowUserView,
    FollowersListView,
    FollowingListView,
)
import profile_app.views as views

urlpatterns = [
    # Profile endpoints
    path('/', ProfileListView.as_view(), name='profile-list'),
    path('<int:pk>/', ProfileDetailView.as_view(), name='profile-details'),
    # path('update/', ProfileUpdateView.as_view(), name='profile-update'),

    # Follow endpoints
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/<int:pk>/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('<int:pk>/followers/', FollowersListView.as_view(), name='followers-list'),
    path('<int:pk>/following/', FollowingListView.as_view(), name='following-list'),

    # Support endpoints
    path('support/', views.support, name='support'),
    path('support/success/', views.support_success, name='support-success'),
]
