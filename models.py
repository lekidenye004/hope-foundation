from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


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
    payment_method = db.Column(db.String(20), default='mpesa')  # mpesa or paypal
    checkout_request_id = db.Column(db.String(100))  # For M-Pesa
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'amount': float(self.amount),
            'donation_type': self.donation_type,
            'message': self.message,
            'transaction_id': self.transaction_id,
            'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }