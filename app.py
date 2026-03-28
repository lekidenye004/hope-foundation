from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, session
from datetime import datetime
import os
import secrets
import uuid

# Create Flask app FIRST
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Database configuration (use SQLite for testing if MySQL fails)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hope_foundation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)


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
    payment_method = db.Column(db.String(20), default='mpesa')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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


# Routes
@app.route('/')
def index():
    return render_template('index.html', active_page='home')


@app.route('/about')
def about():
    return render_template('about.html', active_page='about')


@app.route('/programs')
def programs():
    return render_template('program.html', active_page='programs')


@app.route('/get-involved', methods=['GET', 'POST'])
def get_involved():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        volunteer_type = request.form.get('volunteer_type')
        message = request.form.get('message')

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

    return render_template('involved.html', active_page='get-involved')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        try:
            contact = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(contact)
            db.session.commit()
            flash('Thank you for your message!', 'success')
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
        donation_type = request.form.get('donation_type')
        message = request.form.get('message')

        try:
            amount = float(amount)
            transaction_id = f"DON-{uuid.uuid4().hex[:8].upper()}"

            donation = Donation(
                name=name,
                email=email,
                phone=phone,
                amount=amount,
                donation_type=donation_type or 'one-time',
                message=message,
                transaction_id=transaction_id,
                status='completed'  # For testing
            )
            db.session.add(donation)
            db.session.commit()

            flash(f'Thank you for your donation of KES {amount:.2f}!', 'success')
            return redirect(url_for('donation_success', transaction_id=transaction_id))
        except Exception as e:
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('donate'))

    return render_template('donate.html', active_page='donate')


@app.route('/donation-success/<transaction_id>')
def donation_success(transaction_id):
    donation = Donation.query.filter_by(transaction_id=transaction_id).first()
    return render_template('donation_success.html', donation=donation)


@app.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email')
    if email:
        try:
            subscriber = NewsletterSubscriber(email=email)
            db.session.add(subscriber)
            db.session.commit()
            flash('Successfully subscribed!', 'success')
        except:
            flash('Email already subscribed or invalid.', 'error')
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
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    print("=" * 50)
    print("🚀 Starting Hope Foundation Application")
    print("=" * 50)
    print("📍 http://localhost:5000")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)