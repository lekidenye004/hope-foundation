from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, session
from datetime import datetime
import os
import secrets
import uuid
import requests
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app FIRST
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Database configuration (use SQLite for testing)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hope_foundation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

# M-Pesa Configuration
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', 'xGWs5zvsDsCGOZvGAvXS7gOxCGBw4qlX2BE2vmEnuc7s9xxR')  # Replace with your actual key
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '0ywbqhB0YamJomLh8BHdLx7oBDxx3GTqJCTLAXLY7bEyt0tLo4E8rGxNkDyIGjKG')  # Replace with your actual secret
MPESA_SHORTCODE = "174379"
MPESA_PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', 'https://your-domain.onrender.com/mpesa-callback')

# Store pending transactions (in production, use Redis or database)
pending_transactions = {}


# Define models
class Donation(db.Model):
    __tablename__ = 'donations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    donation_type = db.Column(db.String(20), default='one-time')
    message = db.Column(db.Text)
    transaction_id = db.Column(db.String(100), unique=True)
    checkout_request_id = db.Column(db.String(100))
    receipt_number = db.Column(db.String(50))
    payment_method = db.Column(db.String(20), default='mpesa')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)


class Volunteer(db.Model):
    __tablename__ = 'volunteers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    volunteer_type = db.Column(db.String(50))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='unread')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Create tables
with app.app_context():
    db.create_all()
    print("✅ Database tables created")


# M-Pesa Helper Functions
def get_mpesa_access_token():
    """Get OAuth token from Safaricom"""
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(
            url,
            auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET),
            timeout=30
        )

        if response.status_code == 200:
            token = response.json()['access_token']
            print("✅ Access token obtained successfully")
            return token
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting token: {str(e)}")
        return None


def format_phone_number(phone):
    """Format phone number to 254XXXXXXXXX"""
    phone = phone.replace(' ', '').replace('-', '').replace('+', '')

    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif not phone.startswith('254') and len(phone) == 9:
        phone = '254' + phone

    return phone


def stk_push(phone_number, amount, account_reference, transaction_desc):
    """Send STK push to customer's phone"""
    try:
        # Format phone number
        phone_number = format_phone_number(phone_number)

        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        # Generate password
        password_str = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()

        # Get access token
        access_token = get_mpesa_access_token()
        if not access_token:
            return {"success": False, "message": "Failed to authenticate with M-Pesa"}

        # Prepare payload
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(int(amount)),
            "PartyA": phone_number,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": account_reference[:12],
            "TransactionDesc": transaction_desc[:13]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        print(f"📤 Sending STK Push for KES {amount} to {phone_number}")

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        result = response.json()

        print(f"📥 Response: {result}")

        if response.status_code == 200 and result.get('ResponseCode') == '0':
            return {
                "success": True,
                "checkout_request_id": result['CheckoutRequestID'],
                "message": "Please check your phone and enter your PIN"
            }
        else:
            return {
                "success": False,
                "message": result.get('errorMessage', result.get('ResponseDescription', 'Payment initiation failed'))
            }

    except Exception as e:
        print(f"❌ Error in STK push: {str(e)}")
        return {"success": False, "message": str(e)}


# Routes
@app.route('/')
def index():
    return render_template('index.html', active_page='home')


@app.route('/about')
def about():
    return render_template('about.html', active_page='about')


@app.route('/programs')
def programs():
    return render_template('programs.html', active_page='programs')


@app.route('/get-involved', methods=['GET', 'POST'])
def get_involved():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        volunteer_type = request.form.get('volunteer_type')
        message = request.form.get('message')

        if not name or not email:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('get_involved'))

        try:
            volunteer = Volunteer(
                name=name,
                email=email,
                phone=phone,
                volunteer_type=volunteer_type,
                message=message
            )
            db.session.add(volunteer)
            db.session.commit()
            flash(f'Thank you {name}! We will contact you soon.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('get_involved'))

    return render_template('get-involved.html', active_page='get-involved')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('contact'))

        try:
            contact = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(contact)
            db.session.commit()
            flash('Thank you for your message! We will get back to you soon.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('contact'))

    return render_template('contact.html', active_page='contact')


@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        amount = request.form.get('amount')
        donation_type = request.form.get('donation_type', 'one-time')
        message = request.form.get('message')
        payment_method = request.form.get('payment_method', 'mpesa')

        # Validate inputs
        if not all([name, email, amount]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('donate'))

        try:
            amount = float(amount)
            if amount <= 0:
                flash('Please enter a valid amount.', 'error')
                return redirect(url_for('donate'))
        except ValueError:
            flash('Invalid amount entered.', 'error')
            return redirect(url_for('donate'))

        # For M-Pesa, phone is required
        if payment_method == 'mpesa' and not phone:
            flash('Phone number is required for M-Pesa payments.', 'error')
            return redirect(url_for('donate'))

        # Generate transaction ID
        transaction_id = f"DON-{uuid.uuid4().hex[:8].upper()}"

        if payment_method == 'mpesa':
            # Process M-Pesa payment
            result = stk_push(
                phone_number=phone,
                amount=amount,
                account_reference=f"HopeFdn-{transaction_id[:8]}",
                transaction_desc=f"Donation {name[:13]}"
            )

            if result['success']:
                # Save donation as pending
                donation = Donation(
                    name=name,
                    email=email,
                    phone=phone,
                    amount=amount,
                    donation_type=donation_type,
                    message=message,
                    transaction_id=transaction_id,
                    checkout_request_id=result['checkout_request_id'],
                    payment_method='mpesa',
                    status='pending'
                )
                db.session.add(donation)
                db.session.commit()

                # Store in pending transactions
                pending_transactions[result['checkout_request_id']] = {
                    'donation_id': donation.id,
                    'transaction_id': transaction_id,
                    'name': name,
                    'email': email,
                    'amount': amount
                }

                flash(result['message'], 'info')
                return render_template('payment_pending.html',
                                       checkout_request_id=result['checkout_request_id'],
                                       amount=amount,
                                       phone=phone,
                                       name=name,
                                       transaction_id=transaction_id)
            else:
                flash(f'Payment failed: {result["message"]}', 'error')
                return redirect(url_for('donate'))
        else:
            # For testing without M-Pesa
            donation = Donation(
                name=name,
                email=email,
                phone=phone,
                amount=amount,
                donation_type=donation_type,
                message=message,
                transaction_id=transaction_id,
                payment_method='test',
                status='completed'
            )
            db.session.add(donation)
            db.session.commit()

            flash(f'Thank you for your donation of KES {amount:.2f}!', 'success')
            return redirect(url_for('donation_success', transaction_id=transaction_id))

    return render_template('donate.html', active_page='donate')


@app.route('/mpesa-callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback"""
    try:
        data = request.get_json()

        print("=" * 60)
        print("M-PESA CALLBACK RECEIVED")
        print("=" * 60)

        if data and 'Body' in data and 'stkCallback' in data['Body']:
            callback = data['Body']['stkCallback']
            checkout_request_id = callback.get('CheckoutRequestID')
            result_code = callback.get('ResultCode')
            result_desc = callback.get('ResultDesc')

            print(f"Checkout ID: {checkout_request_id}")
            print(f"Result Code: {result_code}")
            print(f"Result Description: {result_desc}")

            # Find the donation
            donation = Donation.query.filter_by(checkout_request_id=checkout_request_id).first()

            if donation:
                if result_code == 0:  # Payment successful
                    # Get M-Pesa receipt number
                    receipt_number = None
                    if 'CallbackMetadata' in callback:
                        for item in callback['CallbackMetadata']['Item']:
                            if item['Name'] == 'MpesaReceiptNumber':
                                receipt_number = item['Value']
                                break

                    donation.status = 'completed'
                    donation.receipt_number = receipt_number
                    donation.completed_at = datetime.utcnow()
                    db.session.commit()

                    print(f"✅ Payment successful!")
                    print(f"   Donation ID: {donation.transaction_id}")
                    print(f"   Receipt: {receipt_number}")

                else:  # Payment failed
                    donation.status = 'failed'
                    db.session.commit()
                    print(f"❌ Payment failed: {result_desc}")

                # Update pending transactions
                if checkout_request_id in pending_transactions:
                    pending_transactions[checkout_request_id]['status'] = donation.status

        return jsonify({"ResultCode": 0, "ResultDesc": "Success"})

    except Exception as e:
        print(f"Error in callback: {str(e)}")
        return jsonify({"ResultCode": 1, "ResultDesc": str(e)})


@app.route('/check-payment-status/<checkout_request_id>')
def check_payment_status(checkout_request_id):
    """Check payment status via AJAX"""
    donation = Donation.query.filter_by(checkout_request_id=checkout_request_id).first()

    if donation:
        return jsonify({
            'status': donation.status,
            'transaction_id': donation.transaction_id,
            'receipt_number': donation.receipt_number
        })

    return jsonify({'status': 'not_found'})


@app.route('/donation-success/<transaction_id>')
def donation_success(transaction_id):
    donation = Donation.query.filter_by(transaction_id=transaction_id).first()
    if donation:
        return render_template('donation_success.html', donation=donation)
    flash('Donation not found', 'error')
    return redirect(url_for('index'))


@app.route('/payment-pending/<checkout_request_id>')
def payment_pending_page(checkout_request_id):
    """Show payment pending page"""
    donation = Donation.query.filter_by(checkout_request_id=checkout_request_id).first()
    if donation:
        return render_template('payment_pending.html',
                               checkout_request_id=checkout_request_id,
                               amount=donation.amount,
                               phone=donation.phone,
                               name=donation.name,
                               transaction_id=donation.transaction_id)
    return redirect(url_for('donate'))


@app.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email')
    if not email:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        flash('Email is required', 'error')
        return redirect(request.referrer or url_for('index'))

    try:
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if existing:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Email already subscribed'}), 400
            flash('Email already subscribed', 'error')
            return redirect(request.referrer or url_for('index'))

        subscriber = NewsletterSubscriber(email=email)
        db.session.add(subscriber)
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Successfully subscribed!'})
        flash('Successfully subscribed to our newsletter!', 'success')

    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Subscription failed'}), 500
        flash('Subscription failed. Please try again.', 'error')

    return redirect(request.referrer or url_for('index'))


@app.route('/api/donations/stats')
def api_donation_stats():
    from sqlalchemy import func
    total_amount = db.session.query(func.sum(Donation.amount)).scalar() or 0
    total_count = Donation.query.count()
    return jsonify({
        'total_amount': float(total_amount),
        'total_donations': total_count
    })


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.context_processor
def utility_processor():
    return {'current_year': datetime.now().year}


# Run the app
if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)

    print("=" * 50)
    print("🚀 Starting Hope Foundation Application")
    print("=" * 50)
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Check if running on Render
    is_production = os.environ.get('RENDER', False)
    
    if is_production:
        print("📍 Production Mode (Render.com)")
        print(f"📍 Port: {port}")
        # Production: no debug, use gunicorn
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("📍 Development Mode (Local)")
        print("📍 Local: http://localhost:5000")
        print("📍 Network: http://0.0.0.0:5000")
        # Development: debug mode
        app.run(debug=True, host='0.0.0.0', port=port)
    
    print("=" * 50)
