"""
Views for the Apple In-App Purchase (iOS) payment path.

These sit alongside the Stripe subscription views and never touch them:
  * AppleVerifyPurchaseView       — the iOS app posts a signed transaction here
                                     after a StoreKit purchase; we verify it and
                                     activate the user's subscription.
  * AppleServerNotificationView   — Apple posts subscription lifecycle events
                                     (renew/cancel/refund/expire) here.
"""
import logging

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from dmv.api_response import APIResponse, ErrorCodes
from .models import Subscription
from .serializers import SubscriptionSerializer
from .apple_iap_service import AppleIAPService, AppleIAPError

logger = logging.getLogger(__name__)


class AppleVerifyPurchaseView(APIView):
    """
    Verify an Apple In-App Purchase and activate the user's subscription.

    The iOS app sends the StoreKit 2 signed transaction (JWS). We verify it
    against Apple's certificate chain and, if valid, mark the subscription active.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Verify Apple In-App Purchase",
        description=(
            "Verify a StoreKit 2 signed transaction produced by the iOS app after "
            "an In-App Purchase, then activate or update the user's subscription."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "signed_transaction": {
                        "type": "string",
                        "description": "StoreKit 2 signed transaction JWS (Transaction.jwsRepresentation)"
                    }
                },
                "required": ["signed_transaction"],
                "example": {"signed_transaction": "eyJhbGciOiJFUzI1NiIs..."}
            }
        },
        responses={
            200: OpenApiResponse(
                description="Purchase verified and subscription activated",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "error": {"type": "string", "nullable": True, "example": None},
                        "data": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string", "example": "active"},
                                "plan_tier": {"type": "string", "example": "standard"},
                                "current_period_end": {"type": "string", "format": "date-time"},
                                "has_access": {"type": "boolean", "example": True}
                            }
                        }
                    }
                }
            ),
            400: OpenApiResponse(
                description="Missing or invalid signed transaction",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {"type": "string", "example": "signed_transaction is required"},
                        "data": {"type": "object", "nullable": True, "example": None}
                    }
                }
            ),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid"),
        },
        tags=["Subscriptions"],
    )
    def post(self, request):
        signed_transaction = request.data.get('signed_transaction')

        if not signed_transaction:
            return APIResponse.error(
                message="signed_transaction is required",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            subscription = AppleIAPService.activate_subscription(
                user=request.user,
                signed_transaction=signed_transaction,
            )
        except AppleIAPError as e:
            logger.warning(f"Apple IAP verification failed for {request.user.email}: {str(e)}")
            return APIResponse.error(
                message=str(e),
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Unexpected error verifying Apple purchase: {str(e)}", exc_info=True)
            return APIResponse.error(
                message="Failed to verify purchase",
                error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = SubscriptionSerializer(subscription)
        return APIResponse.success(
            data={
                **serializer.data,
                'has_access': subscription.has_access(),
            },
            message="Purchase verified successfully",
        )


@method_decorator(csrf_exempt, name='dispatch')
class AppleServerNotificationView(APIView):
    """
    Handle App Store Server Notifications (V2).

    Apple POSTs a JSON body `{ "signedPayload": "<JWS>" }`. We verify the JWS and
    update the matching subscription. Public + unauthenticated (Apple calls it),
    but every payload is cryptographically verified before it is trusted.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(exclude=True)  # Exclude from API docs (server-to-server)
    def post(self, request):
        signed_payload = request.data.get('signedPayload')

        if not signed_payload:
            logger.error("Apple server notification missing signedPayload")
            return Response({'error': 'Missing signedPayload'}, status=400)

        try:
            AppleIAPService.handle_notification(signed_payload)
            return Response({'status': 'success'})
        except AppleIAPError as e:
            logger.error(f"Invalid Apple server notification: {str(e)}")
            return Response({'error': 'Invalid signature'}, status=400)
        except Exception as e:
            logger.error(f"Error handling Apple notification: {str(e)}", exc_info=True)
            return Response({'error': 'Notification handler failed'}, status=500)
