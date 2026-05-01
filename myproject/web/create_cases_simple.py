import sys
import os
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')
os.chdir(r'c:\Users\Admin\Desktop\project10\backend')

# Set encoding for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import app
from extensions import db
from models.help_case import HelpCase
from models.user import Beneficiary
from datetime import datetime, timedelta
import random

with app.app_context():
    try:
        # Get first beneficiary
        beneficiary = Beneficiary.query.first()
        
        if not beneficiary:
            print("[ERROR] No beneficiary found!")
        else:
            print("[OK] Found beneficiary: %s" % beneficiary.user.full_name)
            
            # Create help cases
            cases_to_create = [
                {
                    'title': 'Emergency Medical Treatment',
                    'description': 'Need urgent medical treatment for serious condition',
                    'category': 'medical',
                    'amount_needed': 5000
                },
                {
                    'title': 'Rent Payment Help',
                    'description': 'Need help with emergency rent payment',
                    'category': 'rent',
                    'amount_needed': 1500
                },
                {
                    'title': 'Education Support',
                    'description': 'Help needed for school fees',
                    'category': 'education',
                    'amount_needed': 2000
                }
            ]
            
            count = 0
            for case_data in cases_to_create:
                # Check if case exists
                existing = HelpCase.query.filter_by(
                    beneficiary_id=beneficiary.id,
                    title=case_data['title']
                ).first()
                
                if not existing:
                    case = HelpCase(
                        beneficiary_id=beneficiary.id,
                        title=case_data['title'],
                        description=case_data['description'],
                        category=case_data['category'],
                        amount_needed=case_data['amount_needed'],
                        amount_raised=random.uniform(100, case_data['amount_needed'] * 0.5),
                        status=random.choice(['pending', 'approved']),
                        urgency_level=random.choice(['low', 'medium', 'high', 'critical']),
                        priority_score=random.uniform(30, 95),
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    db.session.add(case)
                    count += 1
                    print("   [OK] Created: %s" % case_data['title'])
            
            if count > 0:
                db.session.commit()
                print("\n[OK] SUCCESS! Created %d help cases" % count)
                
                # Verify
                total_cases = HelpCase.query.count()
                print("[INFO] Total cases now: %d" % total_cases)
            else:
                print("[WARN] Cases already exist")
        
    except Exception as e:
        print("[ERROR] %s" % str(e))
        import traceback
        traceback.print_exc()
