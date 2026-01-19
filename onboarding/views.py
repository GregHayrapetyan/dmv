from django.shortcuts import render
from django.db.models import Q

from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, OpenApiResponse
from dmv.api_mixins import StandardizedResponseMixin
from .models import State, Vehicle, Profile
from .serializers import StateSerializer, VehicleSerializer, ProfileSerializer

class StateListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List US states that have tests or lessons.
    
    Returns a list of US states that have at least one test or lesson available.
    No authentication required.
    """
    serializer_class = StateSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        # Only return states that have tests or lessons
        return State.objects.filter(
            Q(tests__isnull=False) | Q(lessons__isnull=False)
        ).distinct().order_by("name")

    @extend_schema(
        summary="List states with content",
        description="Retrieve a list of US states that have tests or lessons available.",
        responses={
            200: StateSerializer(many=True),
        },
        tags=["Onboarding"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class VehicleListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List vehicle types that have tests.
    
    Returns a list of vehicle types that have at least one test available.
    No authentication required.
    """
    serializer_class = VehicleSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        # Only return vehicles that have tests
        return Vehicle.objects.filter(
            tests__isnull=False
        ).distinct().order_by("name")

    @extend_schema(
        summary="List vehicle types with content",
        description="Retrieve a list of vehicle types that have tests available.",
        responses={
            200: VehicleSerializer(many=True),
        },
        tags=["Onboarding"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ProfileRetrieveUpdateView(StandardizedResponseMixin, generics.RetrieveUpdateAPIView):
    """
    Get or update user profile.
    
    Retrieves or updates the authenticated user's onboarding profile,
    including state, vehicle type, age, and gender.
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
        description="Update the authenticated user's onboarding profile. Can update state, vehicle type, age, and gender.",
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

    @extend_schema(exclude=True)
    def patch(self, request, *args, **kwargs):
        return APIResponse.error(
            message="PATCH method not allowed. Use PUT instead.",
            error_code=ErrorCodes.METHOD_NOT_ALLOWED,
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    def get_object(self):
        # Profile should already exist via signals, but get_or_create as fallback
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

