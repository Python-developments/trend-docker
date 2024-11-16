from .serializers import ReactionListSerializer
from .models import Reaction
from rest_framework import generics


class ReactionListView(generics.ListAPIView):
    queryset = Reaction.objects.all()
    serializer_class = ReactionListSerializer