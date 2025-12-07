"""
Stripe service for managing subscriptions.
"""
import stripe
from django.conf import settings
from django.utils import timezone
from .models import Subscription
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service class for Stripe operations."""
    
    @staticmethod
    def create_customer(user):
        """Create a Stripe customer for a user."""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.email,
                metadata={'user_id': user.id}
            )
            logger.info(f"Created Stripe customer {customer.id} for user {user.email}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer for {user.email}: {str(e)}")
            raise
    
    @staticmethod
    def get_or_create_customer(user):
        """Get existing Stripe customer or create a new one."""
        try:
            subscription = Subscription.objects.get(user=user)
            return subscription.stripe_customer_id
        except Subscription.DoesNotExist:
            customer = StripeService.create_customer(user)
            Subscription.objects.create(
                user=user,
                stripe_customer_id=customer.id,
                status='incomplete'
            )
            return customer.id
    
    @staticmethod
    def create_checkout_session(user, price_id, success_url, cancel_url):
        """
        Create a Stripe Checkout session for subscription.
        
        Args:
            user: User instance
            price_id: Stripe price ID for the subscription plan
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if user cancels
        
        Returns:
            Checkout session object
        """
        try:
            customer_id = StripeService.get_or_create_customer(user)
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={'user_id': user.id}
            )
            
            logger.info(f"Created checkout session {session.id} for user {user.email}")
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session for {user.email}: {str(e)}")
            raise
    
    @staticmethod
    def create_billing_portal_session(user, return_url):
        """
        Create a Stripe billing portal session for managing subscription.
        
        Args:
            user: User instance
            return_url: URL to return to after portal session
        
        Returns:
            Portal session object
        """
        try:
            subscription = Subscription.objects.get(user=user)
            
            session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=return_url,
            )
            
            logger.info(f"Created billing portal session for user {user.email}")
            return session
        except Subscription.DoesNotExist:
            logger.error(f"No subscription found for user {user.email}")
            raise ValueError("User has no subscription")
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create billing portal session for {user.email}: {str(e)}")
            raise
    
    @staticmethod
    def cancel_subscription(user):
        """Cancel user's subscription at period end."""
        try:
            subscription = Subscription.objects.get(user=user)
            
            if not subscription.stripe_subscription_id:
                raise ValueError("No active subscription to cancel")
            
            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            subscription.cancel_at_period_end = True
            subscription.save(update_fields=['cancel_at_period_end'])
            
            logger.info(f"Cancelled subscription for user {user.email}")
            return stripe_subscription
        except Subscription.DoesNotExist:
            logger.error(f"No subscription found for user {user.email}")
            raise ValueError("User has no subscription")
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription for {user.email}: {str(e)}")
            raise
    
    @staticmethod
    def handle_webhook_event(event):
        """
        Handle Stripe webhook events.
        
        Args:
            event: Stripe event object
        """
        event_type = event['type']
        
        if event_type == 'customer.subscription.created':
            StripeService._handle_subscription_created(event['data']['object'])
        elif event_type == 'customer.subscription.updated':
            StripeService._handle_subscription_updated(event['data']['object'])
        elif event_type == 'customer.subscription.deleted':
            StripeService._handle_subscription_deleted(event['data']['object'])
        elif event_type == 'invoice.payment_succeeded':
            StripeService._handle_payment_succeeded(event['data']['object'])
        elif event_type == 'invoice.payment_failed':
            StripeService._handle_payment_failed(event['data']['object'])
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
    
    @staticmethod
    def _handle_subscription_created(stripe_subscription):
        """Handle subscription.created event."""
        try:
            subscription = Subscription.objects.get(
                stripe_customer_id=stripe_subscription['customer']
            )
            subscription.stripe_subscription_id = stripe_subscription['id']
            subscription.status = stripe_subscription['status']
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                stripe_subscription['current_period_start'], tz=timezone.utc
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                stripe_subscription['current_period_end'], tz=timezone.utc
            )
            subscription.save()
            logger.info(f"Subscription created: {subscription.stripe_subscription_id}")
        except Subscription.DoesNotExist:
            logger.error(f"Subscription not found for customer {stripe_subscription['customer']}")
    
    @staticmethod
    def _handle_subscription_updated(stripe_subscription):
        """Handle subscription.updated event."""
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription['id']
            )
            subscription.status = stripe_subscription['status']
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                stripe_subscription['current_period_start'], tz=timezone.utc
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                stripe_subscription['current_period_end'], tz=timezone.utc
            )
            subscription.cancel_at_period_end = stripe_subscription.get('cancel_at_period_end', False)
            subscription.save()
            logger.info(f"Subscription updated: {subscription.stripe_subscription_id}")
        except Subscription.DoesNotExist:
            logger.error(f"Subscription not found: {stripe_subscription['id']}")
    
    @staticmethod
    def _handle_subscription_deleted(stripe_subscription):
        """Handle subscription.deleted event."""
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription['id']
            )
            subscription.status = 'canceled'
            subscription.save()
            logger.info(f"Subscription deleted: {subscription.stripe_subscription_id}")
        except Subscription.DoesNotExist:
            logger.error(f"Subscription not found: {stripe_subscription['id']}")
    
    @staticmethod
    def _handle_payment_succeeded(invoice):
        """Handle invoice.payment_succeeded event."""
        subscription_id = invoice.get('subscription')
        if subscription_id:
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                # Update subscription status if needed
                if subscription.status != 'active':
                    subscription.status = 'active'
                    subscription.save()
                logger.info(f"Payment succeeded for subscription: {subscription_id}")
            except Subscription.DoesNotExist:
                logger.error(f"Subscription not found: {subscription_id}")
    
    @staticmethod
    def _handle_payment_failed(invoice):
        """Handle invoice.payment_failed event."""
        subscription_id = invoice.get('subscription')
        if subscription_id:
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.status = 'past_due'
                subscription.save()
                logger.warning(f"Payment failed for subscription: {subscription_id}")
            except Subscription.DoesNotExist:
                logger.error(f"Subscription not found: {subscription_id}")
