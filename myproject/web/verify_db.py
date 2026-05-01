import sys
sys.path.insert(0, r'c:\Users\Admin\Desktop\project10\backend')
from app import app
from models.help_case import HelpCase
from models.user import User, Beneficiary, Donor

with app.app_context():
    print('DATABASE STATUS:')
    users = User.query.count()
    beneficiaries = Beneficiary.query.count()
    donors = Donor.query.count()
    cases = HelpCase.query.count()
    
    print(f'Users: {users}')
    print(f'Beneficiaries: {beneficiaries}')
    print(f'Donors: {donors}')
    print(f'Cases: {cases}')
    print()
    
    if cases > 0:
        print('CASES FOUND:')
        for case in HelpCase.query.all()[:5]:
            print(f'  - {case.title}')
    else:
        print('NO CASES FOUND!')
