
from django.urls import path
from .views import ReactionListView
urlpatterns = [
    path('list/', ReactionListView.as_view(), name='reaction-create'),
]