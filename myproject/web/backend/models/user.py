# backend/models/user.py
from . import db, bcrypt
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    language = db.Column(db.String(2), default='en')
    
    # Relationships
    donor_profile = db.relationship('Donor', back_populates='user', uselist=False, cascade='all, delete-orphan')
    beneficiary_profile = db.relationship('Beneficiary', back_populates='user', uselist=False, cascade='all, delete-orphan')
    charity_profile = db.relationship('Charity', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Donor(db.Model):
    __tablename__ = 'donors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    total_donations = db.Column(db.Float, default=0)
    
    # Relationships
    user = db.relationship('User', back_populates='donor_profile')
    donations = db.relationship('Donation', back_populates='donor', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', back_populates='donor', lazy=True, cascade='all, delete-orphan')


class Beneficiary(db.Model):
    __tablename__ = 'beneficiaries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    income = db.Column(db.Float, default=0)
    family_size = db.Column(db.Integer, default=1)
    children_count = db.Column(db.Integer, default=0)
    address = db.Column(db.String(200))
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    
    # Relationships
    user = db.relationship('User', back_populates='beneficiary_profile')
    help_cases = db.relationship('HelpCase', back_populates='beneficiary', lazy=True, cascade='all, delete-orphan')


class Charity(db.Model):
    __tablename__ = 'charities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    registration_number = db.Column(db.String(50))
    verified = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', back_populates='charity_profile')