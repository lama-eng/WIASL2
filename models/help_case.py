# backend/models/help_case.py
from .user import db
from datetime import datetime

class HelpCase(db.Model):
    __tablename__ = 'help_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiaries.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='other')
    amount_needed = db.Column(db.Float)
    amount_raised = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='pending')
    priority_score = db.Column(db.Float, default=0)
    urgency_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text)  # For storing admin requests for more info
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - FIXED: removed the conflicting backref
    documents = db.relationship('Document', back_populates='help_case', lazy=True, cascade='all, delete-orphan')
    donations = db.relationship('Donation', back_populates='case', lazy=True, cascade='all, delete-orphan')
    ai_analysis = db.relationship('AIAnalysis', back_populates='case', uselist=False, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', back_populates='case', lazy=True, cascade='all, delete-orphan')
    
    # Add relationship to beneficiary
    beneficiary = db.relationship('Beneficiary', back_populates='help_cases')


class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('help_cases.id'))
    filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    document_type = db.Column(db.String(50))  # id_proof, income_proof, medical_report, etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified = db.Column(db.Boolean, default=None)  # None = pending, True = verified, False = rejected
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    file_size = db.Column(db.Integer)  # Store file size in bytes
    
    # Relationships - FIXED: using back_populates instead of backref
    help_case = db.relationship('HelpCase', back_populates='documents', foreign_keys=[case_id])
    uploader = db.relationship('User', foreign_keys=[uploaded_by], backref='uploaded_documents')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_documents')


class AIAnalysis(db.Model):
    __tablename__ = 'ai_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('help_cases.id'), unique=True)
    urgency_score = db.Column(db.Float)
    medical_risk_score = db.Column(db.Float)
    children_present = db.Column(db.Boolean)
    detected_category = db.Column(db.String(50))
    priority_score = db.Column(db.Float)
    confidence_score = db.Column(db.Float)
    analyzed_text = db.Column(db.Text)
    full_analysis = db.Column(db.Text)  # Store JSON string
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    case = db.relationship('HelpCase', back_populates='ai_analysis')