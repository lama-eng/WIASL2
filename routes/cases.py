# backend/routes/cases.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import  User, Beneficiary, HelpCase, Document, AIAnalysis
from extensions import db

from services.ai_service import AIService
from datetime import datetime
import os
import json

cases_bp = Blueprint('cases', __name__)
ai_service = AIService()

@cases_bp.route('', methods=['POST'])
@jwt_required()
def create_case():
    """Create a new help case"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if user.role != 'beneficiary':
            return jsonify({'error': 'Only beneficiaries can create cases'}), 403
        
        beneficiary = Beneficiary.query.filter_by(user_id=user.id).first()
        if not beneficiary:
            return jsonify({'error': 'Beneficiary profile not found'}), 404
        
        data = request.get_json()
        
        # Create help case
        case = HelpCase(
            beneficiary_id=beneficiary.id,
            title=data['title'],
            description=data['description'],
            category=data.get('category', 'other'),
            amount_needed=float(data.get('amount_needed', 0)),
            status='pending'
        )
        
        db.session.add(case)
        db.session.flush()
        
        # Run AI analysis
        try:
            case_data = {
                'description': data['description'],
                'income': data.get('income', beneficiary.income),
                'family_size': data.get('family_size', beneficiary.family_size),
                'children_count': data.get('children_count', beneficiary.children_count)
            }
            
            ai_analysis = ai_service.analyze_case_comprehensive(case_data)
            
            # Save AI analysis
            ai_record = AIAnalysis(
                case_id=case.id,
                urgency_score=ai_analysis['urgency']['score'],
                medical_risk_score=ai_analysis['medical_risk']['score'],
                children_present=ai_analysis['children']['present'],
                detected_category=ai_analysis['category']['category'],
                priority_score=ai_analysis['priority_score'],
                confidence_score=ai_analysis['confidence_scores']['overall'],
                analyzed_text=data['description'][:500],
            )
            
            db.session.add(ai_record)
            
            # Update case with AI results
            case.priority_score = ai_analysis['priority_score']
            case.urgency_level = ai_analysis['urgency']['level']
            
        except Exception as e:
            print(f"AI Analysis error: {e}")
            # Continue even if AI fails
        
        db.session.commit()
        
        return jsonify({
            'message': 'Case created successfully',
            'case_id': case.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cases_bp.route('/my-cases', methods=['GET'])
@jwt_required()
def get_my_cases():
    """Get cases for the current beneficiary"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if user.role != 'beneficiary':
            return jsonify({'error': 'Only beneficiaries can view their cases'}), 403
        
        beneficiary = Beneficiary.query.filter_by(user_id=user.id).first()
        if not beneficiary:
            return jsonify({'error': 'Beneficiary profile not found'}), 404
        
        cases = HelpCase.query.filter_by(beneficiary_id=beneficiary.id).order_by(HelpCase.created_at.desc()).all()
        
        case_list = []
        for case in cases:
            case_list.append({
                'id': case.id,
                'title': case.title,
                'description': case.description[:200] + '...' if len(case.description) > 200 else case.description,
                'category': case.category,
                'amount_needed': case.amount_needed,
                'amount_raised': case.amount_raised,
                'status': case.status,
                'urgency_level': case.urgency_level,
                'priority_score': case.priority_score,
                'created_at': case.created_at.isoformat()
            })
        
        return jsonify(case_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cases_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_cases():
    """Get all pending cases with optional filters"""
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        search = request.args.get('search', '')
        priority = request.args.get('priority', 'all')
        date_range = request.args.get('date', 'all')
        
        # Base query - get cases that are pending or more_info
        query = HelpCase.query.filter(HelpCase.status.in_(['pending', 'more_info']))
        
        # Apply status filter
        if status != 'all':
            query = query.filter_by(status=status)
        
        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    HelpCase.title.ilike(f'%{search}%'),
                    HelpCase.description.ilike(f'%{search}%')
                )
            )
        
        # Apply priority filter
        if priority != 'all':
            if priority == 'high':
                query = query.filter(HelpCase.priority_score >= 80)
            elif priority == 'medium':
                query = query.filter(HelpCase.priority_score.between(50, 79))
            elif priority == 'low':
                query = query.filter(HelpCase.priority_score < 50)
        
        # Apply date filter
        today = datetime.utcnow().date()
        if date_range == 'today':
            query = query.filter(db.func.date(HelpCase.created_at) == today)
        elif date_range == 'week':
            week_ago = today - timedelta(days=7)
            query = query.filter(db.func.date(HelpCase.created_at) >= week_ago)
        elif date_range == 'month':
            month_ago = today - timedelta(days=30)
            query = query.filter(db.func.date(HelpCase.created_at) >= month_ago)
        
        # Order by priority score (highest first) and then by creation date
        cases = query.order_by(HelpCase.priority_score.desc(), HelpCase.created_at.desc()).all()
        
        case_list = []
        for case in cases:
            case_data = {
                'id': case.id,
                'title': case.title,
                'description': case.description[:200] + '...' if len(case.description) > 200 else case.description,
                'category': case.category,
                'amount_needed': case.amount_needed,
                'created_at': case.created_at.isoformat(),
                'beneficiary_name': case.beneficiary.user.full_name if case.beneficiary and case.beneficiary.user else 'Unknown',
                'priority_score': case.priority_score,
                'urgency_level': case.urgency_level,
                'status': case.status
            }
            
            # Add AI analysis if exists
            if case.ai_analysis:
                case_data['ai_analysis'] = {
                    'urgency_score': case.ai_analysis.urgency_score,
                    'medical_risk_score': case.ai_analysis.medical_risk_score,
                    'children_present': case.ai_analysis.children_present,
                    'detected_category': case.ai_analysis.detected_category,
                    'confidence_score': case.ai_analysis.confidence_score
                }
            
            case_list.append(case_data)
        
        return jsonify(case_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@cases_bp.route('/approved', methods=['GET'])
@jwt_required()
def get_approved_cases():
    """Get approved cases for donors and admin"""
    try:
        # Get query parameters
        category = request.args.get('category')
        urgency = request.args.get('urgency')
        search = request.args.get('search')
        status = request.args.get('status', 'approved')  # Default to approved
        
        # Base query
        query = HelpCase.query.filter_by(status='approved')
        
        # Apply filters
        if category:
            query = query.filter_by(category=category)
        if urgency:
            query = query.filter_by(urgency_level=urgency)
        if search:
            query = query.filter(
                db.or_(
                    HelpCase.title.ilike(f'%{search}%'),
                    HelpCase.description.ilike(f'%{search}%')
                )
            )
        
        # Order by priority score (highest first)
        cases = query.order_by(HelpCase.priority_score.desc()).all()
        
        case_list = []
        for case in cases:
            # Calculate progress
            progress = (case.amount_raised / case.amount_needed * 100) if case.amount_needed > 0 else 0
            
            case_list.append({
                'id': case.id,
                'title': case.title,
                'description': case.description[:200] + '...' if len(case.description) > 200 else case.description,
                'category': case.category,
                'amount_needed': case.amount_needed,
                'amount_raised': case.amount_raised,
                'progress': round(progress, 1),
                'urgency_level': case.urgency_level,
                'priority_score': case.priority_score,
                'status': case.status,
                'created_at': case.created_at.isoformat() if case.created_at else None,
                'beneficiary_name': case.beneficiary.user.full_name if case.beneficiary and case.beneficiary.user else 'Anonymous'
            })
        
        return jsonify(case_list), 200
        
    except Exception as e:
        print(f"Error in get_approved_cases: {e}")
        return jsonify({'error': str(e)}), 500


@cases_bp.route('/<int:case_id>/request-info', methods=['POST'])
@jwt_required()
def request_more_info(case_id):
    """Admin requests more information for a case"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        notes = data.get('notes', '')
        
        case = HelpCase.query.get_or_404(case_id)
        case.status = 'more_info'
        
        # Store the request notes (you might want to create a separate table for this)
        if hasattr(case, 'admin_notes'):
            case.admin_notes = notes
        
        db.session.commit()
        
        # Here you would also send a notification to the beneficiary
        
        return jsonify({'message': 'Information request sent successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cases_bp.route('/<int:case_id>', methods=['GET'])
@jwt_required()
def get_case_details(case_id):
    """Get detailed information about a specific case"""
    try:
        case = HelpCase.query.get_or_404(case_id)
        
        case_data = {
            'id': case.id,
            'title': case.title,
            'description': case.description,
            'category': case.category,
            'amount_needed': case.amount_needed,
            'amount_raised': case.amount_raised,
            'status': case.status,
            'urgency_level': case.urgency_level,
            'priority_score': case.priority_score,
            'created_at': case.created_at.isoformat(),
            'beneficiary': {
                'name': case.beneficiary.user.full_name if case.beneficiary and case.beneficiary.user else 'Anonymous',
                'location': case.beneficiary.address if case.beneficiary else None
            }
        }
        
        # Add AI analysis if exists
        if case.ai_analysis:
            case_data['ai_analysis'] = {
                'urgency_score': case.ai_analysis.urgency_score,
                'medical_risk_score': case.ai_analysis.medical_risk_score,
                'children_present': case.ai_analysis.children_present,
                'confidence_score': case.ai_analysis.confidence_score
            }
        
        return jsonify(case_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500