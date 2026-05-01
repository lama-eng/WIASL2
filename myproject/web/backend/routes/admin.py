# backend/routes/admin.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import  User, HelpCase, Donation, AIAnalysis
from extensions import db

from datetime import datetime
import json
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        return jsonify(user_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """Update user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'role' in data:
            user.role = data['role']
        
        db.session.commit()
        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/cases/pending', methods=['GET'])
@jwt_required()
@admin_required
def get_pending_cases():
    """Get all pending cases with AI analysis"""
    try:
        cases = HelpCase.query.filter_by(status='pending').order_by(HelpCase.created_at.desc()).all()
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
                'urgency_level': case.urgency_level
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

@admin_bp.route('/cases/<int:case_id>/review', methods=['POST'])
@jwt_required()
@admin_required
def review_case(case_id):
    """Approve or reject a case"""
    try:
        case = HelpCase.query.get_or_404(case_id)
        data = request.get_json()
        
        action = data.get('action')
        notes = data.get('notes', '')
        
        if action == 'approve':
            case.status = 'approved'
            case.approved_at = datetime.utcnow()
            message = 'Case approved successfully'
        elif action == 'reject':
            case.status = 'rejected'
            message = 'Case rejected'
        elif action == 'more_info':
            case.status = 'more_info'
            message = 'More information requested'
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        db.session.commit()
        return jsonify({'message': message}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_dashboard_stats():
    """Get admin dashboard statistics"""
    try:
        total_users = User.query.count()
        total_cases = HelpCase.query.count()
        pending_cases = HelpCase.query.filter_by(status='pending').count()
        approved_cases = HelpCase.query.filter_by(status='approved').count()
        total_donations = db.session.query(db.func.sum(Donation.amount)).scalar() or 0
        
        # Cases by category
        cases_by_category = db.session.query(
            HelpCase.category, db.func.count(HelpCase.id)
        ).group_by(HelpCase.category).all()
        
        # Recent cases
        recent_cases = HelpCase.query.order_by(HelpCase.created_at.desc()).limit(5).all()
        recent_cases_data = []
        for case in recent_cases:
            recent_cases_data.append({
                'id': case.id,
                'title': case.title,
                'status': case.status,
                'created_at': case.created_at.isoformat()
            })
        
        stats = {
            'total_users': total_users,
            'total_cases': total_cases,
            'pending_cases': pending_cases,
            'approved_cases': approved_cases,
            'total_donations': float(total_donations),
            'cases_by_category': [{'category': cat, 'count': count} for cat, count in cases_by_category],
            'recent_cases': recent_cases_data
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500