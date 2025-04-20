import os
from typing import Literal, Tuple, Dict
import stripe
import logging
import datetime

class StripeAdapter:
    PRICE_IDS = {
        '980': 'price_1QDau2GUmbNfqrzFFvHVvoaz',
        '1980': 'price_1QDaxQGUmbNfqrzFniNnEiyF',
        '3980': 'price_1RFb85GUmbNfqrzFReo445kQ'
    }
    # テスト用
    # PRICE_IDS = {
    #     '980': 'price_1QNPhlRo65d8y4fN7jsiQwmf',
    #     '1980': 'price_1QNPhyRo65d8y4fNmYAj1ZSP',
    #     '3980': 'price_1QNPiCRo65d8y4fNwGGoKq6y'
    # }

    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_API_KEY')
        if not stripe.api_key:
            raise ValueError("STRIPE_API_KEY environment variable is not set")
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_customer_id(self, line_user_id: str) -> str:
        customers = stripe.Customer.search(
            query=f"metadata['line_user_id']:'{line_user_id}'",
            limit=1,
        )
        if customers.data:
            return customers.data[0].id
        else:
            new_customer = stripe.Customer.create(metadata={"line_user_id": line_user_id})
            return new_customer.id

    def get_current_subscription(self, customer_id: str) -> stripe.Subscription:
        subscriptions = stripe.Subscription.list(customer=customer_id, status='active', limit=1)
        return subscriptions.data[0] if subscriptions.data else None

    def create_checkout_session(self, line_user_id: str, post_type: Literal['980','1980','3980']) -> str:
        if post_type not in self.PRICE_IDS:
            raise ValueError(f"Invalid subscription type: {post_type}")
        customer_id = self.get_customer_id(line_user_id)
        current_subscription = self.get_current_subscription(customer_id)
        new_price_id = self.PRICE_IDS[post_type]
        try:
            if not current_subscription:
                return self.create_new_subscription(customer_id, new_price_id, line_user_id)
            else:
                raise ValueError("Customer already has an active subscription")
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def create_new_subscription(self, customer_id: str, price_id: str, line_user_id: str) -> str:
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://www.fox-hoken.com/zerocon-ai/',
            cancel_url='https://www.fox-hoken.com/zerocon-ai/',
            metadata={"line_user_id": line_user_id}
        )
        return checkout_session.url

    def create_cancel_session(self, line_user_id: str) -> str:
        customer_id = self.get_customer_id(line_user_id)
        
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url='https://your-return-url.com/'
        )
        return session.url

    def upgrade_subscription(self, subscription_id: str, new_price_id: str):
        try:
            subscription_item_id = stripe.Subscription.retrieve(subscription_id)['items']['data'][0].id
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False,
                proration_behavior='always_invoice',
                items=[{
                    'id': subscription_item_id,
                    'price': new_price_id,
                }],
            )
            self.logger.info(f"Subscription upgraded: {subscription.id}")
            return subscription
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error during upgrade: {e}")
            raise

    def downgrade_subscription(self, subscription_id: str, new_price_id: str):
        try:
            subscription_item = stripe.Subscription.retrieve(subscription_id)['items']['data'][0]
            subscription_item_id = subscription_item.id
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False,
                proration_behavior='none',
                items=[{
                    'id': subscription_item_id,
                    'price': new_price_id,
                }],
                billing_cycle_anchor='unchanged'
            )
            self.logger.info(f"Subscription downgraded: {subscription.id}")
            return subscription
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error during downgrade: {e}")
            raise

    def fetch_checkout_data(self, subscription_id: str) -> Tuple[Dict, str]:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            line_user_id = subscription['metadata'].get('line_user_id', '')
            
            if not line_user_id:
                # customerオブジェクトからline_user_idを取得
                customer = stripe.Customer.retrieve(subscription['customer'])
                line_user_id = customer['metadata'].get('line_user_id', '')
            
            if subscription['items']['data']:
                subscription_item = subscription['items']['data'][0]
                price = subscription_item['price']
                product = stripe.Product.retrieve(price['product'])
                product_info = {
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'price_id': price['id'],
                    'price_amount': price['unit_amount'],
                    'price_currency': price['currency'],
                    'price_interval': price['recurring']['interval'],
                    'price_interval_count': price['recurring']['interval_count']
                }
                self.logger.info(f"LINE User ID: {line_user_id}")
                self.logger.info(f"Product Info: {product_info}")
                return product_info, line_user_id
            else:
                self.logger.warning("No subscription items found")
                return {}, ''
        except stripe.error.StripeError as e:
            self.logger.error(f"An error occurred: {str(e)}")
            return {}, ''
        
    def get_plan_change_date(self,sub_id):
        sub = stripe.Subscription.retrieve(sub_id)
        return datetime.datetime.fromtimestamp(sub.current_period_end, datetime.timezone.utc)