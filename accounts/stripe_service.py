"""
Stripe service for managing subscriptions.
"""
import stripe
from django.conf import settings
from django.utils import timezone
from .models import Subscription, PaymentMethod
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
            # If subscription exists but has no stripe_customer_id, create one
            if not subscription.stripe_customer_id:
                customer = StripeService.create_customer(user)
                subscription.stripe_customer_id = customer.id
                subscription.save()
                return customer.id
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
    def create_checkout_session(user, price_id, success_url, cancel_url, plan_tier=None):
        """
        Create a Stripe Checkout session for a recurring subscription.
        
        Args:
            user: User instance
            price_id: Stripe recurring price ID (7-day/30-day/90-day interval)
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if user cancels
            plan_tier: Plan tier (starter/standard/premium)
        
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
                metadata={
                    'user_id': user.id,
                    'plan_tier': plan_tier or '',
                    'price_id': price_id
                }
            )
            
            logger.info(f"Created subscription checkout session {session.id} for user {user.email}")
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
    def reactivate_subscription(user):
        """Reactivate a subscription that was set to cancel at period end."""
        try:
            subscription = Subscription.objects.get(user=user)
            
            if not subscription.stripe_subscription_id:
                raise ValueError("No subscription to reactivate")
            
            if not subscription.cancel_at_period_end:
                raise ValueError("Subscription is not set to cancel")
            
            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            subscription.cancel_at_period_end = False
            subscription.save(update_fields=['cancel_at_period_end'])
            
            logger.info(f"Reactivated subscription for user {user.email}")
            return stripe_subscription
        except Subscription.DoesNotExist:
            raise ValueError("User has no subscription")
        except stripe.error.StripeError as e:
            logger.error(f"Failed to reactivate subscription for {user.email}: {str(e)}")
            raise
    
    @staticmethod
    def change_plan(user, new_price_id, new_plan_tier):
        """
        Change user's subscription to a different plan (upgrade/downgrade).
        Prorates automatically.
        """
        try:
            subscription = Subscription.objects.get(user=user)
            
            if not subscription.stripe_subscription_id:
                raise ValueError("No active subscription to change")
            
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_sub['items']['data'][0]['id'],
                    'price': new_price_id,
                }],
                proration_behavior='create_prorations',
                metadata={
                    'plan_tier': new_plan_tier,
                }
            )
            
            subscription.stripe_price_id = new_price_id
            subscription.plan_tier = new_plan_tier
            subscription.cancel_at_period_end = False
            subscription.save(update_fields=['stripe_price_id', 'plan_tier', 'cancel_at_period_end'])
            
            logger.info(f"Changed plan for user {user.email} to {new_plan_tier}")
            return stripe_subscription
        except Subscription.DoesNotExist:
            raise ValueError("User has no subscription")
        except stripe.error.StripeError as e:
            logger.error(f"Failed to change plan for {user.email}: {str(e)}")
            raise
    
    @staticmethod
    def create_setup_session(user, return_url):
        """
        Create a Stripe Checkout session in setup mode to update payment method.
        """
        try:
            subscription = Subscription.objects.get(user=user)
            if not subscription.stripe_customer_id:
                raise ValueError("No Stripe customer found")
            
            session = stripe.checkout.Session.create(
                customer=subscription.stripe_customer_id,
                mode='setup',
                payment_method_types=['card'],
                success_url=return_url,
                cancel_url=return_url,
                metadata={
                    'user_id': user.id,
                }
            )
            
            logger.info(f"Created setup session for user {user.email}")
            return session
        except Subscription.DoesNotExist:
            raise ValueError("User has no subscription")
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create setup session for {user.email}: {str(e)}")
            raise
    
    @staticmethod
    def get_payment_details(user):
        """
        Get the user's payment method details from local DB.
        Falls back to Stripe API if not found locally, and syncs the result.
        """
        # Try local DB first
        local_pm = PaymentMethod.objects.filter(user=user, is_default=True).first()
        if not local_pm:
            local_pm = PaymentMethod.objects.filter(user=user).first()
        
        if local_pm:
            return {
                'id': local_pm.stripe_payment_method_id,
                'brand': local_pm.card_brand,
                'last4': local_pm.card_last4,
                'exp_month': local_pm.card_exp_month,
                'exp_year': local_pm.card_exp_year,
                'name': local_pm.billing_name,
            }
        
        # Fallback: fetch from Stripe and sync locally
        try:
            subscription = Subscription.objects.get(user=user)
            if not subscription.stripe_customer_id:
                return None
            
            payment_methods = stripe.PaymentMethod.list(
                customer=subscription.stripe_customer_id,
                type='card',
                limit=1
            )
            
            if payment_methods.data:
                pm = payment_methods.data[0]
                card = pm.card
                StripeService._save_payment_method_locally(user, pm)
                return {
                    'id': pm.id,
                    'brand': card.brand,
                    'last4': card.last4,
                    'exp_month': card.exp_month,
                    'exp_year': card.exp_year,
                    'name': pm.billing_details.name,
                }
            return None
        except Subscription.DoesNotExist:
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get payment details for {user.email}: {str(e)}")
            return None
    
    @staticmethod
    def _save_payment_method_locally(user, stripe_pm, is_default=True):
        """
        Save or update a Stripe PaymentMethod in the local database.
        
        Args:
            user: User instance
            stripe_pm: Stripe PaymentMethod object
            is_default: Whether this is the default payment method
        """
        try:
            card = stripe_pm.card
            if not card:
                logger.warning(f"PaymentMethod {stripe_pm.id} has no card data")
                return None
            
            # If setting as default, unset other defaults for this user
            if is_default:
                PaymentMethod.objects.filter(user=user, is_default=True).update(is_default=False)
            
            pm, created = PaymentMethod.objects.update_or_create(
                stripe_payment_method_id=stripe_pm.id,
                defaults={
                    'user': user,
                    'card_brand': card.brand,
                    'card_last4': card.last4,
                    'card_exp_month': card.exp_month,
                    'card_exp_year': card.exp_year,
                    'billing_name': stripe_pm.billing_details.name if stripe_pm.billing_details else None,
                    'is_default': is_default,
                }
            )
            action = 'Created' if created else 'Updated'
            logger.info(f"{action} local payment method {stripe_pm.id} for user {user.email}")
            return pm
        except Exception as e:
            logger.error(f"Failed to save payment method locally for {user.email}: {str(e)}")
            return None
    
    @staticmethod
    def sync_payment_methods_from_stripe(user):
        """
        Sync all payment methods from Stripe to local DB for a given user.
        """
        try:
            subscription = Subscription.objects.get(user=user)
            if not subscription.stripe_customer_id:
                return
            
            # Get default payment method ID from customer
            customer = stripe.Customer.retrieve(subscription.stripe_customer_id)
            default_pm_id = None
            if customer.invoice_settings and customer.invoice_settings.default_payment_method:
                default_pm_id = customer.invoice_settings.default_payment_method
            
            payment_methods = stripe.PaymentMethod.list(
                customer=subscription.stripe_customer_id,
                type='card'
            )
            
            for pm in payment_methods.data:
                is_default = (pm.id == default_pm_id)
                StripeService._save_payment_method_locally(user, pm, is_default=is_default)
            
            logger.info(f"Synced {len(payment_methods.data)} payment methods for user {user.email}")
        except Subscription.DoesNotExist:
            logger.warning(f"No subscription found for user {user.email} during payment method sync")
        except stripe.error.StripeError as e:
            logger.error(f"Failed to sync payment methods for {user.email}: {str(e)}")
    
    @staticmethod
    def get_billing_info(user):
        """
        Get the user's billing information from Stripe customer.
        """
        try:
            subscription = Subscription.objects.get(user=user)
            if not subscription.stripe_customer_id:
                return None
            
            customer = stripe.Customer.retrieve(subscription.stripe_customer_id)
            return {
                'name': customer.name,
                'email': customer.email,
            }
        except Subscription.DoesNotExist:
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get billing info for {user.email}: {str(e)}")
            return None
    
    @staticmethod
    def update_billing_info(user, name=None, email=None):
        """
        Update the user's billing information on the Stripe customer.
        """
        try:
            subscription = Subscription.objects.get(user=user)
            if not subscription.stripe_customer_id:
                raise ValueError("No Stripe customer found")
            
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if email is not None:
                update_data['email'] = email
            
            if update_data:
                stripe.Customer.modify(
                    subscription.stripe_customer_id,
                    **update_data
                )
                logger.info(f"Updated billing info for user {user.email}")
        except Subscription.DoesNotExist:
            raise ValueError("User has no subscription")
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update billing info for {user.email}: {str(e)}")
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
        elif event_type == 'checkout.session.completed':
            StripeService._handle_checkout_completed(event['data']['object'])
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
    
    @staticmethod
    def _handle_checkout_completed(session):
        """Handle checkout.session.completed event for subscriptions."""
        mode = session.get('mode')
        
        if mode == 'setup':
            StripeService._handle_setup_completed(session)
            return
        
        if mode != 'subscription':
            logger.info(f"Skipping checkout.session.completed for mode: {mode}")
            return
        
        try:
            metadata = session.get('metadata', {})
            user_id = metadata.get('user_id') if metadata else None
            plan_tier = metadata.get('plan_tier') if metadata else None
            price_id = metadata.get('price_id') if metadata else None
            
            if not user_id:
                logger.warning(f"Checkout session {session.get('id')} missing user_id metadata.")
                return
            
            from accounts.models import User
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(f"User with id {user_id} not found for checkout session {session.get('id')}")
                return
            
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                defaults={'stripe_customer_id': session.get('customer')}
            )
            
            subscription.stripe_subscription_id = session.get('subscription')
            subscription.stripe_price_id = price_id
            subscription.plan_tier = plan_tier
            subscription.is_one_time_purchase = False
            subscription.status = 'active'
            
            # Fetch Stripe subscription to populate billing period dates
            if subscription.stripe_subscription_id:
                try:
                    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                    subscription.current_period_start = timezone.datetime.fromtimestamp(
                        stripe_sub['current_period_start'], tz=timezone.utc
                    )
                    subscription.current_period_end = timezone.datetime.fromtimestamp(
                        stripe_sub['current_period_end'], tz=timezone.utc
                    )
                except stripe.error.StripeError as sub_err:
                    logger.warning(f"Could not fetch subscription details after checkout: {str(sub_err)}")
            
            # Set access_duration_days from plan_tier if not already set
            if not subscription.access_duration_days and plan_tier:
                duration_map = {'starter': 7, 'standard': 30, 'premium': 90}
                subscription.access_duration_days = duration_map.get(plan_tier)
            
            subscription.save()
            
            # Save payment method details locally
            try:
                payment_methods = stripe.PaymentMethod.list(
                    customer=session.get('customer'),
                    type='card',
                    limit=1
                )
                if payment_methods.data:
                    StripeService._save_payment_method_locally(
                        user, payment_methods.data[0], is_default=True
                    )
            except Exception as pm_err:
                logger.warning(f"Could not save payment method locally after checkout: {str(pm_err)}")
            
            logger.info(f"Subscription activated for user {user.email}: {plan_tier}")
            
        except Exception as e:
            logger.error(f"Error handling checkout completed: {str(e)}", exc_info=True)
    
    @staticmethod
    def _handle_setup_completed(session):
        """Handle checkout.session.completed in setup mode (payment method update)."""
        try:
            setup_intent_id = session.get('setup_intent')
            if not setup_intent_id:
                logger.warning("Setup session completed without setup_intent")
                return
            
            setup_intent = stripe.SetupIntent.retrieve(setup_intent_id)
            payment_method_id = setup_intent.payment_method
            customer_id = session.get('customer')
            
            if not customer_id or not payment_method_id:
                logger.warning("Setup session missing customer or payment_method")
                return
            
            # Set as default payment method on customer
            stripe.Customer.modify(
                customer_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            # Also update the subscription's default payment method if exists
            try:
                subscription = Subscription.objects.get(stripe_customer_id=customer_id)
                if subscription.stripe_subscription_id:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        default_payment_method=payment_method_id
                    )
                
                # Save payment method details locally
                stripe_pm = stripe.PaymentMethod.retrieve(payment_method_id)
                StripeService._save_payment_method_locally(
                    subscription.user, stripe_pm, is_default=True
                )
            except Subscription.DoesNotExist:
                pass
            
            logger.info(f"Payment method updated for customer {customer_id}")
            
        except Exception as e:
            logger.error(f"Error handling setup completed: {str(e)}", exc_info=True)
