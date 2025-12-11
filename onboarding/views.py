from django.shortcuts import render

from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, OpenApiResponse
from dmv.api_mixins import StandardizedResponseMixin
from .models import State, Vehicle, Knowledge, Profile
from .serializers import StateSerializer, VehicleSerializer, KnowledgeSerializer, ProfileSerializer

class StateListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all US states.
    
    Returns a list of all available US states for user selection during onboarding.
    No authentication required.
    """
    queryset = State.objects.all().order_by("name")
    serializer_class = StateSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

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

class VehicleListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all vehicle types.
    
    Returns a list of all available vehicle types for user selection during onboarding.
    No authentication required.
    """
    queryset = Vehicle.objects.all().order_by("name")
    serializer_class = VehicleSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    @extend_schema(
        summary="List all vehicle types",
        description="Retrieve a list of all vehicle types available for user profile selection.",
        responses={
            200: VehicleSerializer(many=True),
        },
        tags=["Onboarding"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class KnowledgeListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all knowledge levels.
    
    Returns a list of all available knowledge levels for user selection during onboarding.
    No authentication required.
    """
    queryset = Knowledge.objects.all().order_by("name")
    serializer_class = KnowledgeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    @extend_schema(
        summary="List all knowledge levels",
        description="Retrieve a list of all knowledge levels available for user profile selection.",
        responses={
            200: KnowledgeSerializer(many=True),
        },
        tags=["Onboarding"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ProfileRetrieveUpdateView(StandardizedResponseMixin, generics.RetrieveUpdateAPIView):
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

