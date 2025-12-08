from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import PricingPlan, ClientReview
from .serializers import PricingPlanSerializer, ClientReviewSerializer
from dmv.api_response import APIResponse


class ClientReviewListAPIView(generics.ListAPIView):
    """
    API endpoint to retrieve all active client reviews.
    GET /api/site-details/reviews/
    
    Returns:
        200: List of active client reviews
    """
    serializer_class = ClientReviewSerializer
    permission_classes = [AllowAny]
    
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

