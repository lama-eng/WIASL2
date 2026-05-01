# backend/models/__init__.py

from extensions import db, bcrypt

from .user import User, Donor, Beneficiary, Charity
from .help_case import HelpCase, Document, AIAnalysis
from .donation import Donation, Favorite
