import sys
import os
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')
os.chdir(r'c:\Users\Admin\Desktop\project10\backend')

from app import app
from extensions import db
from models.user import User, Donor, Beneficiary
from models.help_case import HelpCase, AIAnalysis
from models.donation import Donation
from datetime import datetime, timedelta
import random

with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables verified\n")
        
        # Create additional beneficiary and donor users
        users_data = [
            # Additional beneficiaries
            {
                'email': 'ahmed.ahmed@example.com',
                'password': 'password@123',
                'full_name': 'Ahmed Mohammed',
                'phone': '+212-600-123456',
                'role': 'beneficiary',
                'profile_data': {
                    'income': 3500.00,
                    'family_size': 5,
                    'children_count': 3,
                    'address': '789 Oak Avenue, Cairo'
                }
            },
            {
                'email': 'fatima.ali@example.com',
                'password': 'password@123',
                'full_name': 'Fatima Ali',
                'phone': '+966-500-234567',
                'role': 'beneficiary',
                'profile_data': {
                    'income': 2800.00,
                    'family_size': 4,
                    'children_count': 2,
                    'address': '456 Palm Street, Riyadh'
                }
            },
            {
                'email': 'mohammad.hassan@example.com',
                'password': 'password@123',
                'full_name': 'Mohammad Hassan',
                'phone': '+971-50-1234567',
                'role': 'beneficiary',
                'profile_data': {
                    'income': 2200.00,
                    'family_size': 6,
                    'children_count': 4,
                    'address': '321 Pearl Road, Dubai'
                }
            },
            # Additional donors
            {
                'email': 'alice.smith@example.com',
                'password': 'password@123',
                'full_name': 'Alice Smith',
                'phone': '+1-555-1111',
                'role': 'donor'
            },
            {
                'email': 'bob.johnson@example.com',
                'password': 'password@123',
                'full_name': 'Bob Johnson',
                'phone': '+1-555-2222',
                'role': 'donor'
            },
            {
                'email': 'emma.wilson@example.com',
                'password': 'password@123',
                'full_name': 'Emma Wilson',
                'phone': '+1-555-3333',
                'role': 'donor'
            }
        ]
        
        # Create users if they don't exist
        created_beneficiaries = []
        created_donors = []
        
        for user_data in users_data:
            if not User.query.filter_by(email=user_data['email']).first():
                user = User(
                    email=user_data['email'],
                    full_name=user_data['full_name'],
                    phone=user_data['phone'],
                    role=user_data['role'],
                    is_active=True,
                    language='en'
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                db.session.flush()
                
                if user_data['role'] == 'beneficiary':
                    profile = Beneficiary(
                        user_id=user.id,
                        income=user_data['profile_data']['income'],
                        family_size=user_data['profile_data']['family_size'],
                        children_count=user_data['profile_data']['children_count'],
                        address=user_data['profile_data'].get('address', '')
                    )
                    db.session.add(profile)
                    created_beneficiaries.append((user, profile))
                    print(f"✅ Created beneficiary: {user.full_name}")
                else:
                    profile = Donor(user_id=user.id, total_donations=0)
                    db.session.add(profile)
                    created_donors.append((user, profile))
                    print(f"✅ Created donor: {user.full_name}")
        
        # Get existing beneficiary
        existing_beneficiary = Beneficiary.query.first()
        if existing_beneficiary:
            created_beneficiaries.insert(0, (existing_beneficiary.user, existing_beneficiary))
        
        # Create help cases for beneficiaries
        case_templates = [
            {
                'title': 'Medical Treatment for Spinal Surgery',
                'description': 'I need urgent spinal surgery to treat a herniated disc that is causing severe back pain and limiting my ability to work. The surgery costs $8,500 and is not covered by insurance.',
                'category': 'medical',
                'amount_needed': 8500,
                'urgency': 'critical'
            },
            {
                'title': 'Emergency Rent and Utilities Payment',
                'description': 'Lost my job 2 months ago and unable to pay rent and utilities for my family of 4. Need immediate assistance to avoid eviction.',
                'category': 'rent',
                'amount_needed': 3200,
                'urgency': 'high'
            },
            {
                'title': 'University Tuition for Engineering Student',
                'description': 'My son is an excellent student who got accepted to engineering university, but we cannot afford the tuition fees for this semester.',
                'category': 'education',
                'amount_needed': 4500,
                'urgency': 'high'
            },
            {
                'title': 'Emergency Food Assistance',
                'description': 'Single mother of 3 children living below poverty line. Need help to buy food and basic necessities for the month.',
                'category': 'food',
                'amount_needed': 800,
                'urgency': 'critical'
            },
            {
                'title': 'Dialysis Treatment Fund',
                'description': 'My father requires regular dialysis treatments which cost $600 per week. Insurance covers only 50%. Need help to cover the remaining costs.',
                'category': 'medical',
                'amount_needed': 6000,
                'urgency': 'critical'
            },
            {
                'title': 'Generator and Fuel for Off-Grid Living',
                'description': 'Our community has no access to electricity. A used generator costs $1,200 and would provide power for essential needs.',
                'category': 'other',
                'amount_needed': 1200,
                'urgency': 'medium'
            },
            {
                'title': 'School Supplies and Books for 4 Children',
                'description': 'My children need school uniforms, books, and supplies for the new school year. Total cost is $500.',
                'category': 'education',
                'amount_needed': 500,
                'urgency': 'medium'
            },
            {
                'title': 'Clean Water Well for Village',
                'description': 'Our village has no access to clean drinking water. Drilling a well would cost $3,500 and serve 50+ families.',
                'category': 'other',
                'amount_needed': 3500,
                'urgency': 'high'
            }
        ]
        
        # Create cases for beneficiaries
        case_count = 0
        for i, (user, beneficiary) in enumerate(created_beneficiaries):
            # Create 2-3 cases per beneficiary
            num_cases = random.randint(2, 3)
            for j in range(num_cases):
                case_template = case_templates[(i * 3 + j) % len(case_templates)]
                
                # Check if case doesn't already exist
                existing_case = HelpCase.query.filter_by(
                    beneficiary_id=beneficiary.id,
                    title=case_template['title']
                ).first()
                
                if not existing_case:
                    case = HelpCase(
                        beneficiary_id=beneficiary.id,
                        title=case_template['title'],
                        description=case_template['description'],
                        category=case_template['category'],
                        amount_needed=case_template['amount_needed'],
                        amount_raised=random.uniform(0, case_template['amount_needed'] * 0.7),
                        status=random.choice(['pending', 'pending', 'approved', 'approved']),
                        urgency_level=case_template['urgency'],
                        priority_score=random.uniform(40, 95),
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                    )
                    db.session.add(case)
                    db.session.flush()
                    
                    # Create AI Analysis for the case
                    ai_analysis = AIAnalysis(
                        case_id=case.id,
                        urgency_score=random.uniform(60, 100) if case_template['urgency'] in ['critical', 'high'] else random.uniform(30, 70),
                        medical_risk_score=random.uniform(50, 95) if case_template['category'] == 'medical' else random.uniform(10, 50),
                        children_present=beneficiary.children_count > 0,
                        detected_category=case_template['category'],
                        priority_score=case.priority_score,
                        confidence_score=random.uniform(0.75, 0.99)
                    )
                    db.session.add(ai_analysis)
                    
                    case_count += 1
                    print(f"   ✅ Created case: {case_template['title'][:50]}...")
        
        # Create donations
        print(f"\n📊 Creating donations data...")
        donors = Donor.query.all()
        cases = HelpCase.query.filter_by(status='approved').all()
        
        donation_count = 0
        for case in cases[:5]:  # Create donations for first 5 approved cases
            for _ in range(random.randint(2, 5)):
                donor = random.choice(donors) if donors else None
                if donor:
                    amount = random.choice([50, 100, 150, 200, 250, 500])
                    donation = Donation(
                        donor_id=donor.id,
                        case_id=case.id,
                        amount=amount,
                        payment_method=random.choice(['card', 'paypal', 'bank']),
                        status='completed',
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    db.session.add(donation)
                    donor.total_donations += amount
                    donation_count += 1
        
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ DUMMY DATA CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   • Created {len(created_beneficiaries)} beneficiary accounts")
        print(f"   • Created {len(created_donors)} donor accounts")
        print(f"   • Created {case_count} help cases")
        print(f"   • Created {donation_count} donations")
        
        print(f"\n📋 Beneficiary Accounts Created:")
        for user, beneficiary in created_beneficiaries:
            print(f"   • {user.full_name}")
            print(f"     Email: {user.email} | Password: password@123")
            print(f"     Family Size: {beneficiary.family_size} | Children: {beneficiary.children_count}")
        
        print(f"\n💰 Donor Accounts Created:")
        for user, donor in created_donors:
            print(f"   • {user.full_name}")
            print(f"     Email: {user.email} | Password: password@123")
        
        print(f"\n👨‍💼 Admin Account:")
        print(f"   • Email: admin@example.com | Password: admin123")
        
        print("\n" + "="*60)
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
