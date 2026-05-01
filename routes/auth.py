# backend/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import  User, Donor, Beneficiary, Charity
from extensions import db

from datetime import timedelta
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Validate password strength
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Create user
        user = User(
            email=data['email'],
            full_name=data['full_name'],
            phone=data.get('phone', ''),
            role=data['role']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Create role-specific profile
        if data['role'] == 'donor':
            donor = Donor(user_id=user.id)
            db.session.add(donor)
        elif data['role'] == 'beneficiary':
            beneficiary = Beneficiary(
                user_id=user.id,
                income=float(data.get('income', 0)),
                family_size=int(data.get('family_size', 1)),
                children_count=int(data.get('children_count', 0)),
                address=data.get('address', '')
            )
            db.session.add(beneficiary)
        elif data['role'] == 'charity':
            charity = Charity(
                user_id=user.id,
                registration_number=data.get('registration_number', '')
            )
            db.session.add(charity)
        
        db.session.commit()
        
        return jsonify({'message': 'User created successfully', 'user_id': user.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            if not user.is_active:
                return jsonify({'error': 'Account is deactivated'}), 403
                
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={'role': user.role, 'name': user.full_name},
                expires_delta=timedelta(days=1)
            )
            return jsonify({
                'token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.full_name,
                    'role': user.role
                }
            }), 200
        
        return jsonify({'error': 'Invalid email or password'}), 401
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile_data = {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'phone': user.phone,
            'role': user.role,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        
        # Add role-specific data
        if user.role == 'beneficiary' and user.beneficiary_profile:
            benef = user.beneficiary_profile
            profile_data.update({
                'income': benef.income,
                'family_size': benef.family_size,
                'children_count': benef.children_count,
                'address': benef.address
            })
        elif user.role == 'donor' and user.donor_profile:
            donor = user.donor_profile
            profile_data.update({
                'total_donations': donor.total_donations
            })
        
        return jsonify(profile_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}
        if 'full_name' in data and data['full_name'].strip():
            user.full_name = data['full_name'].strip()
        if 'phone' in data:
            user.phone = data['phone']

        if user.role == 'beneficiary' and user.beneficiary_profile:
            benef = user.beneficiary_profile
            if 'income' in data:
                benef.income = float(data['income'])
            if 'family_size' in data:
                benef.family_size = int(data['family_size'])
            if 'children_count' in data:
                benef.children_count = int(data['children_count'])
            if 'address' in data:
                benef.address = data['address']

        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'current_password and new_password are required'}), 400

        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401

        if len(data['new_password']) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400

        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500