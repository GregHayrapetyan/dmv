from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiParameter
from django.core.mail import send_mail
from django.conf import settings

from .models import PricingPlan, ClientReview, Contact, ContactInfo, Partner, MainBanner, HowItWorks, TrustSafety, SuccessSteps
from .serializers import PricingPlanSerializer, ClientReviewSerializer, ContactSerializer, ContactInfoSerializer, PartnerSerializer, MainBannerSerializer, HowItWorksSerializer, TrustSafetySerializer, SuccessStepsSerializer
from dmv.api_response import APIResponse


@extend_schema_view(
    get=extend_schema(
        summary="List client reviews",
        description="Retrieve all active client reviews. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
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
    throttle_classes = []  # No rate limiting for public data
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
        description="Retrieve all active pricing plans with their features. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
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
    throttle_classes = []  # No rate limiting for public pricing data
    
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
        Create a new contact submission and send email notification.
        """
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Invalid contact form data",
                details=serializer.errors
            )
        
        contact = serializer.save()
        
        # Send email notification
        try:
            subject = f"New Contact Form Submission from {contact.name}"
            message = f"""
New contact form submission received:

Name: {contact.name}
Email: {contact.email}
Phone: {contact.phone}

Message:
{contact.message}

---
Submitted at: {contact.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Failed to send contact notification email: {str(e)}")
        
        return APIResponse.success(
            data=serializer.data,
            message="Thank you for contacting us. We will get back to you soon.",
            status_code=status.HTTP_201_CREATED
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get contact information",
        description="Retrieve active contact information for the Contact Us page.",
        tags=["Site Details"],
    )
)
class ContactInfoRetrieveAPIView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve contact information.
    GET /api/site-details/contact-info/
    
    Returns the active contact information (address, phones, emails).
    No authentication required.
    
    Returns:
        200: Active contact information
        404: No active contact information found
    """
    serializer_class = ContactInfoSerializer
    permission_classes = [AllowAny]
    throttle_classes = []  # No rate limiting for public data
    
    def get_object(self):
        """
        Return the active ContactInfo instance.
        """
        try:
            return ContactInfo.objects.get(is_active=True)
        except ContactInfo.DoesNotExist:
            # Return first available if no active one exists
            return ContactInfo.objects.first()
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to use standardized response format.
        """
        instance = self.get_object()
        
        if not instance:
            return APIResponse.error(
                message="Contact information not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return APIResponse.success(data=serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="List partners",
        description="Retrieve all active partners/sponsors. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
        tags=["Site Details"],
    )
)
class PartnerListAPIView(generics.ListAPIView):
    """
    API endpoint to retrieve all active partners.
    GET /api/site-details/partners/
    
    Returns:
        200: List of active partners with logos and descriptions
    """
    serializer_class = PartnerSerializer
    permission_classes = [AllowAny]
    throttle_classes = []  # No rate limiting for public data
    pagination_class = None
    
    def get_queryset(self):
        """
        Return only active partners, ordered by display order.
        """
        return Partner.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        """
        Override list to use standardized response format.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return APIResponse.success(data=serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="Get main banner content",
        description="Retrieve active main banner content. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
        tags=["Site Details"],
    )
)
class MainBannerRetrieveAPIView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve main banner content.
    GET /api/site-details/main-banner/
    
    Returns the active main banner content (image, titles, description, stats, button).
    No authentication required.
    
    Returns:
        200: Active main banner content
        404: No active main banner content found
    """
    serializer_class = MainBannerSerializer
    permission_classes = [AllowAny]
    throttle_classes = []  # No rate limiting for public data
    
    def get_object(self):
        """
        Return the active MainBanner instance.
        """
        try:
            return MainBanner.objects.get(is_active=True)
        except MainBanner.DoesNotExist:
            # Return first available if no active one exists
            return MainBanner.objects.first()
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to use standardized response format.
        """
        instance = self.get_object()
        
        if not instance:
            return APIResponse.error(
                message="Main banner content not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return APIResponse.success(data=serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="Get How It Works section",
        description="Retrieve active How It Works section with all steps. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
        tags=["Site Details"],
    )
)
class HowItWorksRetrieveAPIView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve How It Works section content.
    GET /api/site-details/how-it-works/
    
    Returns the active How It Works section with all steps.
    No authentication required.
    
    Returns:
        200: Active How It Works section with steps
        404: No active How It Works section found
    """
    serializer_class = HowItWorksSerializer
    permission_classes = [AllowAny]
    throttle_classes = []  # No rate limiting for public data
    
    def get_object(self):
        """
        Return the active HowItWorks instance with prefetched steps.
        """
        try:
            return HowItWorks.objects.prefetch_related('steps').get(is_active=True)
        except HowItWorks.DoesNotExist:
            # Return first available if no active one exists
            return HowItWorks.objects.prefetch_related('steps').first()
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to use standardized response format.
        """
        instance = self.get_object()
        
        if not instance:
            return APIResponse.error(
                message="How It Works section not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return APIResponse.success(data=serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="Get Trust & Safety section",
        description="Retrieve active Trust & Safety section with all features. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
        tags=["Site Details"],
    )
)
class TrustSafetyRetrieveAPIView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve Trust & Safety section content.
    GET /api/site-details/trust-safety/
    
    Returns the active Trust & Safety section with all features.
    No authentication required.
    
    Returns:
        200: Active Trust & Safety section with features
        404: No active Trust & Safety section found
    """
    serializer_class = TrustSafetySerializer
    permission_classes = [AllowAny]
    throttle_classes = []  # No rate limiting for public data
    
    def get_object(self):
        """
        Return the active TrustSafety instance with prefetched features.
        """
        try:
            return TrustSafety.objects.prefetch_related('features').get(is_active=True)
        except TrustSafety.DoesNotExist:
            # Return first available if no active one exists
            return TrustSafety.objects.prefetch_related('features').first()
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to use standardized response format.
        """
        instance = self.get_object()
        
        if not instance:
            return APIResponse.error(
                message="Trust & Safety section not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance, context={'request': request})
        return APIResponse.success(data=serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="Get Success Steps section",
        description="Retrieve active Success Steps section with all steps. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
        tags=["Site Details"],
    )
)
class SuccessStepsRetrieveAPIView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve Success Steps section content.
    GET /api/site-details/success-steps/
    
    Returns the active Success Steps section with all steps.
    No authentication required.
    
    Returns:
        200: Active Success Steps section with steps
        404: No active Success Steps section found
    """
    serializer_class = SuccessStepsSerializer
    permission_classes = [AllowAny]
    throttle_classes = []  # No rate limiting for public data
    
    def get_object(self):
        """
        Return the active SuccessSteps instance with prefetched steps.
        """
        try:
            return SuccessSteps.objects.prefetch_related('steps').get(is_active=True)
        except SuccessSteps.DoesNotExist:
            # Return first available if no active one exists
            return SuccessSteps.objects.prefetch_related('steps').first()
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to use standardized response format.
        """
        instance = self.get_object()
        
        if not instance:
            return APIResponse.error(
                message="Success Steps section not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return APIResponse.success(data=serializer.data)
