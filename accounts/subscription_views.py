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

from django.db import models
from dmv.api_response import APIResponse, ErrorCodes
from .models import Subscription, PaymentMethod
from .serializers import SubscriptionSerializer, PaymentMethodSerializer
from .stripe_service import StripeService
from site_details.models import PricingPlan

logger = logging.getLogger(__name__)


class CreateCheckoutSessionView(APIView):
    """
    Create a Stripe Checkout session for recurring subscription.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Create subscription checkout session",
        description="Create a Stripe Checkout session for a recurring subscription (7-day/30-day/90-day billing cycle).",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "price_id": {"type": "string", "description": "Stripe recurring price ID"},
                    "success_url": {"type": "string", "description": "URL to redirect after success"},
                    "cancel_url": {"type": "string", "description": "URL to redirect if cancelled"},
                    "plan_tier": {"type": "string", "description": "Plan tier", "enum": ["starter", "standard", "premium"]}
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
            200: OpenApiResponse(
                description="Checkout session created successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Stripe Checkout session ID", "example": "cs_test_a1b2c3d4"},
                                "url": {"type": "string", "format": "uri", "description": "Stripe-hosted checkout page URL to redirect the user to", "example": "https://checkout.stripe.com/c/pay/cs_test_a1b2c3d4"},
                                "publishable_key": {"type": "string", "description": "Stripe publishable key for client-side use", "example": "pk_test_xxx"}
                            }
                        }
                    }
                }
            ),
            400: OpenApiResponse(
                description="Validation error — missing or invalid fields",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "price_id, success_url, and cancel_url are required"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
            500: OpenApiResponse(
                description="Failed to create checkout session due to a Stripe or server error",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "Failed to create checkout session"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
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

        # Guard: refuse a new Stripe purchase while an active Apple sub exists (would double-bill).
        existing = Subscription.objects.filter(user=request.user).first()
        if existing and existing.conflicts_with_purchase_on('stripe'):
            return APIResponse.error(
                message="You already have an active subscription purchased through Apple. Manage it in the App Store.",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_409_CONFLICT
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
            200: OpenApiResponse(
                description="Billing portal session created successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "format": "uri", "description": "Stripe-hosted billing portal URL to redirect the user to", "example": "https://billing.stripe.com/p/session/test_abc123"}
                            }
                        }
                    }
                }
            ),
            400: OpenApiResponse(
                description="Validation error — return_url is missing",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "return_url is required"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
            404: OpenApiResponse(
                description="No Stripe customer found for this user",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "No Stripe customer found"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            500: OpenApiResponse(
                description="Failed to create billing portal session due to a Stripe or server error",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "Failed to create billing portal session"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
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
            200: OpenApiResponse(
                description="Subscription status retrieved successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {
                            "type": "object",
                            "description": "Subscription fields plus computed access flag",
                            "properties": {
                                "id": {"type": "integer", "description": "Subscription record ID", "example": 1},
                                "status": {"type": "string", "description": "Subscription status", "enum": ["active", "canceled", "past_due", "incomplete", "trialing"], "example": "active"},
                                "plan_tier": {"type": "string", "description": "Plan tier", "enum": ["starter", "standard", "premium"], "example": "standard"},
                                "access_duration_days": {"type": "integer", "description": "Billing cycle length in days", "example": 30},
                                "current_period_start": {"type": "string", "format": "date-time", "description": "Start of current billing period"},
                                "current_period_end": {"type": "string", "format": "date-time", "description": "End of current billing period"},
                                "cancel_at_period_end": {"type": "boolean", "description": "Whether subscription is set to cancel at period end", "example": False},
                                "plan_display_name": {"type": "string", "nullable": True, "description": "Human-friendly plan name", "example": "Standard Plan"},
                                "days_remaining": {"type": "integer", "description": "Days remaining in current billing period", "example": 15},
                                "next_payment_date": {"type": "string", "format": "date-time", "nullable": True, "description": "Next payment date (null if cancelling)"},
                                "created_at": {"type": "string", "format": "date-time"},
                                "updated_at": {"type": "string", "format": "date-time"},
                                "has_access": {"type": "boolean", "description": "Whether the user currently has active access", "example": True}
                            }
                        }
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
            404: OpenApiResponse(
                description="No subscription found for this user",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "No subscription found"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
        },
        tags=["Subscriptions"],
    )
    def get(self, request):
        try:
            subscription = Subscription.objects.get(user=request.user)
            
            # Sync from Stripe if status is stale or period dates missing
            if subscription.status == 'incomplete' or not subscription.current_period_end:
                synced = StripeService.sync_subscription_from_stripe(request.user)
                if synced:
                    subscription = synced
            
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
            200: OpenApiResponse(
                description="Subscription scheduled for cancellation at period end",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            400: OpenApiResponse(
                description="No active subscription to cancel",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "No active subscription to cancel"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
            500: OpenApiResponse(
                description="Failed to cancel subscription due to a Stripe or server error",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "Failed to cancel subscription"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
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


class SubscriptionDetailView(APIView):
    """
    Get full subscription detail including plan, billing info, and payment details.
    This powers the subscription management page.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Get full subscription details",
        description="Get plan info, billing info, and payment details for the subscription management page.",
        responses={
            200: OpenApiResponse(
                description="Full subscription details including plan, billing info, and payment details",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {
                            "type": "object",
                            "properties": {
                                "plan": {
                                    "type": "object",
                                    "description": "Subscription plan details",
                                    "properties": {
                                        "id": {"type": "integer", "example": 1},
                                        "status": {"type": "string", "enum": ["active", "canceled", "past_due", "incomplete", "trialing"], "example": "active"},
                                        "plan_tier": {"type": "string", "enum": ["starter", "standard", "premium"], "example": "standard"},
                                        "access_duration_days": {"type": "integer", "example": 30},
                                        "current_period_start": {"type": "string", "format": "date-time"},
                                        "current_period_end": {"type": "string", "format": "date-time"},
                                        "cancel_at_period_end": {"type": "boolean", "example": False},
                                        "plan_display_name": {"type": "string", "nullable": True, "example": "Standard Plan"},
                                        "days_remaining": {"type": "integer", "example": 15},
                                        "next_payment_date": {"type": "string", "format": "date-time", "nullable": True},
                                        "created_at": {"type": "string", "format": "date-time"},
                                        "updated_at": {"type": "string", "format": "date-time"},
                                        "has_access": {"type": "boolean", "example": True}
                                    }
                                },
                                "billing_info": {
                                    "type": "object",
                                    "nullable": True,
                                    "description": "Billing contact info from Stripe customer record (null if unavailable)",
                                    "properties": {
                                        "name": {"type": "string", "nullable": True, "description": "Billing name", "example": "John Smith"},
                                        "email": {"type": "string", "format": "email", "nullable": True, "description": "Billing email", "example": "john@example.com"}
                                    }
                                },
                                "payment_details": {
                                    "type": "object",
                                    "nullable": True,
                                    "description": "Payment method on file (null if no card saved)",
                                    "properties": {
                                        "id": {"type": "string", "description": "Stripe PaymentMethod ID", "example": "pm_1abc2def3ghi"},
                                        "brand": {"type": "string", "description": "Card brand", "example": "visa"},
                                        "last4": {"type": "string", "description": "Last 4 digits of card number", "example": "4242"},
                                        "exp_month": {"type": "integer", "description": "Card expiration month", "example": 12},
                                        "exp_year": {"type": "integer", "description": "Card expiration year", "example": 2027},
                                        "name": {"type": "string", "nullable": True, "description": "Cardholder name", "example": "John Smith"}
                                    }
                                }
                            }
                        }
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
            404: OpenApiResponse(
                description="No subscription found for this user",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "No subscription found"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
        },
        tags=["Subscriptions"],
    )
    def get(self, request):
        try:
            subscription = Subscription.objects.get(user=request.user)
            
            # Sync from Stripe if status is stale or period dates missing
            if subscription.status == 'incomplete' or not subscription.current_period_end:
                synced = StripeService.sync_subscription_from_stripe(request.user)
                if synced:
                    subscription = synced
            
            serializer = SubscriptionSerializer(subscription)
            
            billing_info = StripeService.get_billing_info(request.user)
            
            # Get payment details from local DB
            default_pm = PaymentMethod.objects.filter(user=request.user, is_default=True).first()
            if not default_pm:
                default_pm = PaymentMethod.objects.filter(user=request.user).first()
            payment_details = PaymentMethodSerializer(default_pm).data if default_pm else None
            
            # Look up the active pricing plan matching the subscription's stripe price
            pricing_plan = PricingPlan.objects.filter(
                is_active=True,
            ).filter(
                models.Q(stripe_price_id_monthly=subscription.stripe_price_id) |
                models.Q(stripe_price_id_one_time=subscription.stripe_price_id)
            ).first()

            plan_data = {
                **serializer.data,
                'has_access': subscription.has_access(),
                'stripe_price_id_monthly': pricing_plan.stripe_price_id_monthly if pricing_plan else None,
                'stripe_price_id_one_time': pricing_plan.stripe_price_id_one_time if pricing_plan else None,
            }

            return APIResponse.success(
                data={
                    'plan': plan_data,
                    'billing_info': billing_info,
                    'payment_details': payment_details,
                },
                message="Subscription details retrieved successfully"
            )
        except Subscription.DoesNotExist:
            return APIResponse.error(
                message="No subscription found",
                error_code=ErrorCodes.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )


class ReactivateSubscriptionView(APIView):
    """
    Reactivate a subscription that was set to cancel at period end.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Reactivate subscription",
        description="Reactivate a subscription that was set to cancel at the end of the billing period.",
        responses={
            200: OpenApiResponse(
                description="Subscription reactivated — cancellation reversed",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            400: OpenApiResponse(
                description="Subscription cannot be reactivated (not pending cancellation or already cancelled)",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "Subscription is not pending cancellation"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
            500: OpenApiResponse(
                description="Failed to reactivate subscription due to a Stripe or server error",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "Failed to reactivate subscription"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
        },
        tags=["Subscriptions"],
    )
    def post(self, request):
        try:
            StripeService.reactivate_subscription(request.user)
            
            return APIResponse.success(
                message="Subscription reactivated successfully"
            )
        except ValueError as e:
            return APIResponse.error(
                message=str(e),
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error reactivating subscription: {str(e)}")
            return APIResponse.error(
                message="Failed to reactivate subscription",
                error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChangePlanView(APIView):
    """
    Change subscription plan (upgrade or downgrade).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Change subscription plan",
        description="Upgrade or downgrade the subscription to a different plan. Prorates automatically.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "price_id": {"type": "string", "description": "New Stripe recurring price ID"},
                    "plan_tier": {"type": "string", "description": "New plan tier", "enum": ["starter", "standard", "premium"]}
                },
                "required": ["price_id", "plan_tier"],
                "example": {
                    "price_id": "price_1234567890",
                    "plan_tier": "premium"
                }
            }
        },
        responses={
            200: OpenApiResponse(
                description="Plan changed successfully with proration applied",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            400: OpenApiResponse(
                description="Validation error — missing fields, invalid plan_tier, or no active subscription",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "plan_tier must be one of: starter, standard, premium"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
            500: OpenApiResponse(
                description="Failed to change plan due to a Stripe or server error",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "Failed to change plan"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
        },
        tags=["Subscriptions"],
    )
    def post(self, request):
        new_price_id = request.data.get('price_id')
        new_plan_tier = request.data.get('plan_tier')
        
        if not new_price_id or not new_plan_tier:
            return APIResponse.error(
                message="price_id and plan_tier are required",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if new_plan_tier not in ['starter', 'standard', 'premium']:
            return APIResponse.error(
                message="plan_tier must be one of: starter, standard, premium",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Guard: an Apple sub can't be changed through Stripe — direct the user to Apple.
        existing = Subscription.objects.filter(user=request.user).first()
        if existing and existing.conflicts_with_purchase_on('stripe'):
            return APIResponse.error(
                message="You already have an active subscription purchased through Apple. Manage it in the App Store.",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_409_CONFLICT
            )

        try:
            StripeService.change_plan(request.user, new_price_id, new_plan_tier)
            
            return APIResponse.success(
                message=f"Plan changed to {new_plan_tier} successfully"
            )
        except ValueError as e:
            return APIResponse.error(
                message=str(e),
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error changing plan: {str(e)}")
            return APIResponse.error(
                message="Failed to change plan",
                error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdatePaymentMethodView(APIView):
    """
    Create a Stripe setup session to update the payment method (card).
    Returns a URL to redirect the user to Stripe's hosted page.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Update payment method",
        description="Create a Stripe setup session to update the card on file. Returns a URL to redirect the user.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "return_url": {"type": "string", "description": "URL to return to after updating payment method"}
                },
                "required": ["return_url"],
                "example": {
                    "return_url": "https://yourapp.com/account"
                }
            }
        },
        responses={
            200: OpenApiResponse(
                description="Stripe setup session created for updating payment method",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Stripe SetupIntent session ID", "example": "seti_1abc2def3ghi"},
                                "url": {"type": "string", "format": "uri", "description": "Stripe-hosted page URL to update card", "example": "https://checkout.stripe.com/c/setup/cs_test_xyz"}
                            }
                        }
                    }
                }
            ),
            400: OpenApiResponse(
                description="Validation error — return_url is missing or no Stripe customer found",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "return_url is required"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
            500: OpenApiResponse(
                description="Failed to create setup session due to a Stripe or server error",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "Failed to create setup session"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
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
            session = StripeService.create_setup_session(
                user=request.user,
                return_url=return_url
            )
            
            return APIResponse.success(
                data={
                    'session_id': session.id,
                    'url': session.url,
                },
                message="Setup session created successfully"
            )
        except ValueError as e:
            return APIResponse.error(
                message=str(e),
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating setup session: {str(e)}")
            return APIResponse.error(
                message="Failed to create setup session",
                error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateBillingInfoView(APIView):
    """
    Update billing information (name, email) on the Stripe customer.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Update billing information",
        description="Update the billing name and/or email on the Stripe customer record.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Billing name"},
                    "email": {"type": "string", "format": "email", "description": "Billing email"}
                },
                "example": {
                    "name": "John Smith",
                    "email": "jsmith@gmail.com"
                }
            }
        },
        responses={
            200: OpenApiResponse(
                description="Billing information updated on Stripe customer record",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            400: OpenApiResponse(
                description="Validation error — no fields provided or no Stripe customer found",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "At least one of name or email is required"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
            500: OpenApiResponse(
                description="Failed to update billing information due to a Stripe or server error",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "Failed to update billing information"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
        },
        tags=["Subscriptions"],
    )
    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        
        if not name and not email:
            return APIResponse.error(
                message="At least one of name or email is required",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            StripeService.update_billing_info(
                user=request.user,
                name=name,
                email=email
            )
            
            return APIResponse.success(
                message="Billing information updated successfully"
            )
        except ValueError as e:
            return APIResponse.error(
                message=str(e),
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating billing info: {str(e)}")
            return APIResponse.error(
                message="Failed to update billing information",
                error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Handle Stripe webhook events.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = []
    
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
