from django.shortcuts import render

from rest_framework import generics, permissions
from .models import State, Profile
from .serializers import StateSerializer, ProfileSerializer

class StateListView(generics.ListAPIView):
    queryset = State.objects.all().order_by("name")
    serializer_class = StateSerializer
    permission_classes = [permissions.AllowAny]

class ProfileRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

