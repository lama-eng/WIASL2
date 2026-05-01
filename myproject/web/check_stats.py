import sys
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')
from app import app
from models.help_case import HelpCase
from models.user import User
from models.donation import Donation

with app.app_context():
    try:
        total_users = User.query.count()
        total_cases = HelpCase.query.count()
        pending = HelpCase.query.filter_by(status='pending').count()
        approved = HelpCase.query.filter_by(status='approved').count()
        donations = Donation.query.count()
        
        print("[STATS]")
        print("Total Users: %d" % total_users)
        print("Total Cases: %d" % total_cases)
        print("Pending Cases: %d" % pending)
        print("Approved Cases: %d" % approved)
        print("Total Donations: %d" % donations)
        
        # Show first 5 cases
        print("\n[SAMPLE CASES]")
        for case in HelpCase.query.limit(5):
            print("  %s | Status: %s" % (case.title[:40], case.status))
            
    except Exception as e:
        print("[ERROR] %s" % str(e))
