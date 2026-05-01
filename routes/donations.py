# backend/routes/donations.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import  User, Donor, HelpCase, Donation, Favorite
from extensions import db

from datetime import datetime
import uuid

donations_bp = Blueprint('donations', __name__)

@donations_bp.route('', methods=['POST'])
@jwt_required()
def create_donation():
    """Create a new donation"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if user.role != 'donor':
            return jsonify({'error': 'Only donors can make donations'}), 403
        
        donor = Donor.query.filter_by(user_id=user.id).first()
        if not donor:
            return jsonify({'error': 'Donor profile not found'}), 404
        
        data = request.get_json()
        case_id = data.get('case_id')
        amount = data.get('amount')
        
        if not case_id or not amount:
            return jsonify({'error': 'Case ID and amount are required'}), 400
        
        case = HelpCase.query.get(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        if case.status != 'approved':
            return jsonify({'error': 'Cannot donate to unapproved case'}), 400
        
        # Create donation
        donation = Donation(
            donor_id=donor.id,
            case_id=case.id,
            amount=amount,
            payment_method=data.get('payment_method', 'card'),
            transaction_id=str(uuid.uuid4()),
            status='completed'  # In production, verify payment first
        )
        
        db.session.add(donation)
        
        # Update case amount raised
        case.amount_raised = (case.amount_raised or 0) + amount
        
        # Update donor total
        donor.total_donations = (donor.total_donations or 0) + amount
        
        # Check if case is fully funded
        if case.amount_raised >= case.amount_needed:
            case.status = 'funded'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Donation successful',
            'donation_id': donation.id,
            'transaction_id': donation.transaction_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@donations_bp.route('/my-donations', methods=['GET'])
@jwt_required()
def get_my_donations():
    """Get donor's donation history"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if user.role != 'donor':
            return jsonify({'error': 'Only donors can view donations'}), 403
        
        donor = Donor.query.filter_by(user_id=user.id).first()
        if not donor:
            return jsonify({'error': 'Donor profile not found'}), 404
        
        donations = Donation.query.filter_by(donor_id=donor.id).order_by(Donation.created_at.desc()).all()
        
        donation_list = []
        for donation in donations:
            donation_list.append({
                'id': donation.id,
                'amount': donation.amount,
                'case_title': donation.case.title if donation.case else 'Unknown',
                'case_id': donation.case_id,
                'transaction_id': donation.transaction_id,
                'status': donation.status,
                'created_at': donation.created_at.isoformat()
            })
        
        return jsonify(donation_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@donations_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    """Get donor's favorite cases"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if user.role != 'donor':
            return jsonify({'error': 'Only donors can have favorites'}), 403
        
        donor = Donor.query.filter_by(user_id=user.id).first()
        if not donor:
            return jsonify({'error': 'Donor profile not found'}), 404
        
        favorites = Favorite.query.filter_by(donor_id=donor.id).all()
        
        favorite_list = []
        for fav in favorites:
            case = fav.case
            if case:
                favorite_list.append({
                    'id': fav.id,
                    'case_id': case.id,
                    'case_title': case.title,
                    'case_description': case.description[:100] + '...' if len(case.description) > 100 else case.description,
                    'amount_needed': case.amount_needed,
                    'amount_raised': case.amount_raised,
                    'urgency_level': case.urgency_level,
                    'created_at': fav.created_at.isoformat()
                })
        
        return jsonify(favorite_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@donations_bp.route('/favorites/<int:case_id>', methods=['POST'])
@jwt_required()
def add_favorite(case_id):
    """Add case to favorites"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if user.role != 'donor':
            return jsonify({'error': 'Only donors can add favorites'}), 403
        
        donor = Donor.query.filter_by(user_id=user.id).first()
        if not donor:
            return jsonify({'error': 'Donor profile not found'}), 404
        
        case = HelpCase.query.get(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        # Check if already favorited
        existing = Favorite.query.filter_by(donor_id=donor.id, case_id=case_id).first()
        if existing:
            return jsonify({'error': 'Case already in favorites'}), 400
        
        favorite = Favorite(donor_id=donor.id, case_id=case_id)
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({'message': 'Added to favorites'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@donations_bp.route('/favorites/<int:case_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite(case_id):
    """Remove case from favorites"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if user.role != 'donor':
            return jsonify({'error': 'Only donors can remove favorites'}), 403
        
        donor = Donor.query.filter_by(user_id=user.id).first()
        if not donor:
            return jsonify({'error': 'Donor profile not found'}), 404
        
        favorite = Favorite.query.filter_by(donor_id=donor.id, case_id=case_id).first()
        if not favorite:
            return jsonify({'error': 'Favorite not found'}), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({'message': 'Removed from favorites'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500