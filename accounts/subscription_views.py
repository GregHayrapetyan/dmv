"""
Views for managing Stripe subscriptions.
"""
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

from dmv.api_response import APIResponse, ErrorCodes
from .models import Subscription
from .serializers import SubscriptionSerializer
from .stripe_service import StripeService

logger = logging.getLogger(__name__)


class CreateCheckoutSessionView(APIView):
    """
    Create a Stripe Checkout session for subscription.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Create subscription checkout session",
        description="Create a Stripe Checkout session to subscribe to premium content.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "price_id": {"type": "string", "description": "Stripe price ID"},
                    "success_url": {"type": "string", "description": "URL to redirect after success"},
                    "cancel_url": {"type": "string", "description": "URL to redirect if cancelled"},
                    "plan_tier": {"type": "string", "description": "Plan tier (starter/standard/premium) for one-time purchases", "enum": ["starter", "standard", "premium"]}
                },
                "required": ["price_id", "success_url", "cancel_url"],
                "example": {
                    "price_id": "price_1234567890",
                    "success_url": "https://yourapp.com/success",
                    "cancel_url": "https://yourapp.com/cancel",
                    "plan_tier": "standard"
                }
            }
        },
        responses={
            200: OpenApiResponse(description="Checkout session created"),
            400: OpenApiResponse(description="Invalid request"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Subscriptions"],
    )
    def post(self, request):
        price_id = request.data.get('price_id')
        success_url = request.data.get('success_url')
        cancel_url = request.data.get('cancel_url')
        plan_tier = request.data.get('plan_tier')  # Optional: starter/standard/premium
        
        if not all([price_id, success_url, cancel_url]):
            return APIResponse.error(
                message="price_id, success_url, and cancel_url are required",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate plan_tier if provided
        if plan_tier and plan_tier not in ['starter', 'standard', 'premium']:
            return APIResponse.error(
                message="plan_tier must be one of: starter, standard, premium",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = StripeService.create_checkout_session(
                user=request.user,
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                plan_tier=plan_tier
            )
            
            return APIResponse.success(
                data={
                    'session_id': session.id,
                    'url': session.url,
                    'publishable_key': settings.STRIPE_PUBLISHABLE_KEY
                },
                message="Checkout session created successfully"
            )
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return APIResponse.error(
                message="Failed to create checkout session",
                error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateBillingPortalSessionView(APIView):
    """
    Create a Stripe billing portal session for managing subscription.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Create billing portal session",
        description="Create a Stripe billing portal session to manage subscription (cancel, update payment method, etc.).",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "return_url": {"type": "string", "description": "URL to return to after portal session"}
                },
                "required": ["return_url"],
                "example": {
                    "return_url": "https://yourapp.com/account"
                }
            }
        },
        responses={
            200: OpenApiResponse(description="Portal session created"),
            400: OpenApiResponse(description="Invalid request or no subscription"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Subscriptions"],
    )
    def post(self, request):
        return_url = request.data.get('return_url')
        
        if not return_url:
            return APIResponse.error(
                message="return_url is required",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = StripeService.create_billing_portal_session(
                user=request.user,
                return_url=return_url
            )
            
            return APIResponse.success(
                data={'url': session.url},
                message="Billing portal session created successfully"
            )
        except ValueError as e:
            return APIResponse.error(
                message=str(e),
                error_code=ErrorCodes.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error creating billing portal session: {str(e)}")
            return APIResponse.error(
                message="Failed to create billing portal session",
                error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionStatusView(APIView):
    """
    Get current subscription status for authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Get subscription status",
        description="Retrieve the current subscription status for the authenticated user.",
        responses={
            200: SubscriptionSerializer,
            404: OpenApiResponse(description="No subscription found"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Subscriptions"],
    )
    def get(self, request):
        try:
            subscription = Subscription.objects.get(user=request.user)
            serializer = SubscriptionSerializer(subscription)
            
            return APIResponse.success(
                data={
                    **serializer.data,
                    'has_access': subscription.has_access()
                },
                message="Subscription status retrieved successfully"
            )
        except Subscription.DoesNotExist:
            return APIResponse.error(
                message="No subscription found",
                error_code=ErrorCodes.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )


class CancelSubscriptionView(APIView):
    """
    Cancel subscription at the end of the current billing period.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Cancel subscription",
        description="Cancel the subscription at the end of the current billing period. Access continues until period end.",
        responses={
            200: OpenApiResponse(description="Subscription cancelled"),
            400: OpenApiResponse(description="No active subscription"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Subscriptions"],
    )
    def post(self, request):
        try:
            StripeService.cancel_subscription(request.user)
            
            return APIResponse.success(
                message="Subscription will be cancelled at the end of the current billing period"
            )
        except ValueError as e:
            return APIResponse.error(
                message=str(e),
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return APIResponse.error(
                message="Failed to cancel subscription",
                error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Handle Stripe webhook events.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(exclude=True)  # Exclude from API docs
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            return Response({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return Response({'error': 'Invalid signature'}, status=400)
        
        # Handle the event
        try:
            StripeService.handle_webhook_event(event)
            return Response({'status': 'success'})
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return Response({'error': 'Webhook handler failed'}, status=500)
