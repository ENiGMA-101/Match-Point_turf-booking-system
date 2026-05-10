from django.conf import settings
from decimal import Decimal
from datetime import datetime
from .models import Payment

class SimplePaymentGateway:
    
    def __init__(self):
        self.payment_methods = {
            'bkash': {'name': 'bKash', 'color': '#E2136E'},
            'nagad': {'name': 'Nagad', 'color': '#F7941D'},
            'upay': {'name': 'Upay', 'color': '#00A651'}
        }

    def process_payment(self, booking, payment_method, mobile, pin):
        
        if not self._validate_mobile(mobile):
            return {'success': False, 'message': 'Invalid mobile number format'}
        
        if not self._validate_pin(pin):
            return {'success': False, 'message': 'PIN must be 4 digits'}
        
        if payment_method not in self.payment_methods:
            return {'success': False, 'message': 'Invalid payment method'}

        try:
            transaction_id = self._generate_transaction_id(payment_method)
                        
            payment, created = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'payment_method': payment_method,
                    'mobile_number': mobile,
                    'transaction_id': transaction_id,
                    'amount': booking.total_cost,
                    'status': 'Completed'
                }
            )
            
            booking.status = 'Confirmed'
            booking.save()
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'payment_method': self.payment_methods[payment_method]['name'],
                'amount': booking.total_cost,
                'booking': booking
            }
            
        except Exception as e:
            return {'success': False, 'message': 'Payment processing failed'}

    def _validate_mobile(self, mobile):
        if not mobile:
            return False
        mobile = mobile.replace(' ', '').replace('-', '')
        return len(mobile) == 11 and mobile.startswith('01') and mobile.isdigit()

    def _validate_pin(self, pin):
        return pin and len(pin) == 4 and pin.isdigit()

    def _generate_transaction_id(self, payment_method):
        prefixes = {'bkash': 'BK', 'nagad': 'NG', 'upay': 'UP'}
        prefix = prefixes.get(payment_method, 'TXN')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}{timestamp}{hash(timestamp) % 1000:03d}"

payment_service = SimplePaymentGateway()