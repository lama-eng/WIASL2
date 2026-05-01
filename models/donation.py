# backend/models/donation.py
from . import db
from datetime import datetime

class Donation(db.Model):
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('help_cases.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    receipt_url = db.Column(db.String(500))
    
    # Relationships
    donor = db.relationship('Donor', back_populates='donations')
    case = db.relationship('HelpCase', back_populates='donations')


class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('help_cases.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('donor_id', 'case_id', name='unique_favorite'),)
    
    # Relationships
    donor = db.relationship('Donor', back_populates='favorites')
    case = db.relationship('HelpCase', back_populates='favorites')