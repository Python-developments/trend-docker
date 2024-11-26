from django.urls import path
from .views import (
    ProfileViewList,
    ProfileDetails,
    FollowUserView,
    UnfollowUserView,
    FollowersListAPIView,
    FollowingListAPIView,
    ProfileUpdateView
)
import profile_app.views as views

urlpatterns = [
    # Profile endpoints
    path('/', ProfileViewList.as_view(), name='profile-list'),
    path('<int:pk>/', ProfileDetails.as_view(), name='profile-details'),
    path('update/', ProfileUpdateView.as_view(), name='profile-update'),

    # Follow endpoints
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/<int:pk>/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('<int:pk>/followers/', FollowersListAPIView.as_view(), name='followers-list'),
    path('<int:pk>/following/', FollowingListAPIView.as_view(), name='following-list'),

    # Support endpoints
    path('support/', views.support, name='support'),
    path('support/success/', views.support_success, name='support-success'),
]
