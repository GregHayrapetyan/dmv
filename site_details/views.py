from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import PricingPlan, ClientReview, Contact
from .serializers import PricingPlanSerializer, ClientReviewSerializer, ContactSerializer
from dmv.api_response import APIResponse


@extend_schema_view(
    get=extend_schema(
        summary="List client reviews",
        description="Retrieve all active client reviews.",
        tags=["Site Details"],
    )
)
class ClientReviewListAPIView(generics.ListAPIView):
    """
    API endpoint to retrieve all active client reviews.
    GET /api/site-details/reviews/
    
    Returns:
        200: List of active client reviews
    """
    serializer_class = ClientReviewSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    
    def get_queryset(self):
        """
        Return only active reviews, ordered by display order.
        """
        return ClientReview.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        """
        Override list to use standardized response format.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return APIResponse.success(data=serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="List pricing plans",
        description="Retrieve all active pricing plans with their features.",
        tags=["Site Details"],
    )
)
class PricingPlanListAPIView(generics.ListAPIView):
    """
    API endpoint to retrieve all active pricing plans with features.
    GET /api/site-details/pricing-plans/
    
    Returns:
        200: List of active pricing plans with nested features
    """
    serializer_class = PricingPlanSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """
        Return only active plans with their features.
        Prefetch related features for optimal performance.
        """
        return PricingPlan.objects.filter(is_active=True).prefetch_related('features')
    
    def list(self, request, *args, **kwargs):
        """
        Override list to use standardized response format.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return APIResponse.success(data=serializer.data)


class ContactCreateAPIView(generics.CreateAPIView):
    """
    API endpoint to create a contact form submission.
    POST /api/site-details/contact/
    
    Accepts contact form data and creates a new contact record.
    No authentication required.
    
    Returns:
        201: Contact submission created successfully
        400: Validation error
    """
    serializer_class = ContactSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Submit contact form",
        description="Submit a contact form message. No authentication required.",
        request=ContactSerializer,
        responses={
            201: OpenApiResponse(description="Contact submission created successfully"),
            400: OpenApiResponse(description="Validation error"),
        },
        tags=["Site Details"],
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new contact submission.
        """
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Invalid contact form data",
                details=serializer.errors
            )
        
        serializer.save()
        
        return APIResponse.success(
            data=serializer.data,
            message="Thank you for contacting us. We will get back to you soon.",
            status_code=status.HTTP_201_CREATED
        )

