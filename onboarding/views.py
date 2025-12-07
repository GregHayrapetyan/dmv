from django.shortcuts import render

from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import State, Profile
from .serializers import StateSerializer, ProfileSerializer

class StateListView(generics.ListAPIView):
    """
    List all US states.
    
    Returns a list of all available US states for user selection during onboarding.
    No authentication required.
    """
    queryset = State.objects.all().order_by("name")
    serializer_class = StateSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="List all states",
        description="Retrieve a list of all US states available for user profile selection.",
        responses={
            200: StateSerializer(many=True),
        },
        tags=["Onboarding"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ProfileRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile.
    
    Retrieves or updates the authenticated user's onboarding profile,
    including state, vehicle type, and knowledge level.
    Profile is automatically created when user registers.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get user profile",
        description="Retrieve the authenticated user's onboarding profile. Profile is auto-created if it doesn't exist.",
        responses={
            200: ProfileSerializer,
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Onboarding"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update user profile",
        description="Update the authenticated user's onboarding profile. Can update state, vehicle type, and knowledge level.",
        request=ProfileSerializer,
        responses={
            200: ProfileSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Onboarding"],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update user profile",
        description="Partially update the authenticated user's onboarding profile.",
        request=ProfileSerializer,
        responses={
            200: ProfileSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Onboarding"],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        # Profile should already exist via signals, but get_or_create as fallback
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

