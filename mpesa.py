import requests
import json
import base64
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class MpesaAPI:
    def __init__(self):
        self.environment = os.environ.get('MPESA_ENVIRONMENT', 'sandbox')
        self.consumer_key = os.environ.get('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET')
        self.shortcode = os.environ.get('MPESA_SHORTCODE')
        self.passkey = os.environ.get('MPESA_PASSKEY')
        self.callback_url = os.environ.get('MPESA_CALLBACK_URL')

        # API URLs
        if self.environment == 'sandbox':
            self.auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
            self.stk_push_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
            self.query_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'
        else:
            self.auth_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
            self.stk_push_url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
            self.query_url = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'

    def get_access_token(self):
        """Get OAuth access token from Safaricom"""
        try:
            response = requests.get(
                self.auth_url,
                auth=(self.consumer_key, self.consumer_secret)
            )
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                print(f"Failed to get token: {response.text}")
                return None
        except Exception as e:
            print(f"Error getting access token: {str(e)}")
            return None

    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK Push to customer's phone"""
        try:
            # Format phone number (remove 0 or +254)
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+'):
                phone_number = phone_number[1:]

            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

            # Generate password
            password_str = f"{self.shortcode}{self.passkey}{timestamp}"
            password = base64.b64encode(password_str.encode()).decode()

            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'message': 'Failed to get access token'}

            # Prepare headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # Prepare payload
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),
                'PartyA': phone_number,
                'PartyB': self.shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }

            # Make request
            response = requests.post(
                self.stk_push_url,
                headers=headers,
                json=payload
            )

            result = response.json()

            if response.status_code == 200 and 'CheckoutRequestID' in result:
                return {
                    'success': True,
                    'checkout_request_id': result['CheckoutRequestID'],
                    'message': 'Please check your phone to complete payment'
                }
            else:
                return {
                    'success': False,
                    'message': result.get('errorMessage', 'Payment initiation failed')
                }

        except Exception as e:
            print(f"Error in STK push: {str(e)}")
            return {'success': False, 'message': str(e)}

    def query_status(self, checkout_request_id):
        """Query status of STK Push transaction"""
        try:
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

            # Generate password
            password_str = f"{self.shortcode}{self.passkey}{timestamp}"
            password = base64.b64encode(password_str.encode()).decode()

            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'message': 'Failed to get access token'}

            # Prepare headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # Prepare payload
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }

            # Make request
            response = requests.post(
                self.query_url,
                headers=headers,
                json=payload
            )

            return response.json()

        except Exception as e:
            print(f"Error querying status: {str(e)}")
            return {'success': False, 'message': str(e)}