# backend/routes/documents.py
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Beneficiary, HelpCase, Document
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
import mimetypes

documents_bp = Blueprint('documents', __name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Ensure upload folder exists"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@documents_bp.route('/upload', methods=['POST', 'OPTIONS'])
@jwt_required()
def upload_document():
    """Upload documents for a case"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if user.role != 'beneficiary':
            return jsonify({'error': 'Only beneficiaries can upload documents'}), 403
        
        # Get form data
        case_id = request.form.get('case_id')
        document_type = request.form.get('document_type')
        notes = request.form.get('notes', '')
        
        if not case_id or not document_type:
            return jsonify({'error': 'Case ID and document type are required'}), 400
        
        # Check if case exists
        case = HelpCase.query.get(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        # Check if user owns this case
        beneficiary = Beneficiary.query.filter_by(user_id=user.id).first()
        if not beneficiary or case.beneficiary_id != beneficiary.id:
            return jsonify({'error': 'Unauthorized - You do not own this case'}), 403
        
        # Check if files were uploaded
        if 'documents' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('documents')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        ensure_upload_folder()
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                return jsonify({'error': f'File {file.filename} exceeds 10MB limit'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': f'File {file.filename} has unsupported format'}), 400
            
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            new_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
            
            # Create case-specific folder
            case_folder = os.path.join(UPLOAD_FOLDER, f"case_{case_id}")
            os.makedirs(case_folder, exist_ok=True)
            
            file_path = os.path.join(case_folder, new_filename)
            file.save(file_path)
            
            # Save to database
            document = Document(
                case_id=case_id,
                filename=original_filename,
                file_path=file_path,
                document_type=document_type,
                notes=notes,
                uploaded_by=user.id,
                file_size=file_size,
                verified=None  # None = pending
            )
            
            db.session.add(document)
            uploaded_files.append({
                'id': document.id,
                'filename': original_filename,
                'document_type': document_type,
                'file_size': file_size
            })
        
        # Update case status if it was in 'more_info' state
        if case.status == 'more_info':
            case.status = 'pending'
            case.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Documents uploaded successfully',
            'files': uploaded_files
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/my-documents', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_my_documents():
    """Get all documents for the current user"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        documents = []
        
        if user.role == 'beneficiary':
            # Get documents for beneficiary's cases
            beneficiary = Beneficiary.query.filter_by(user_id=user.id).first()
            if not beneficiary:
                return jsonify([]), 200
            
            cases = HelpCase.query.filter_by(beneficiary_id=beneficiary.id).all()
            case_ids = [c.id for c in cases]
            
            docs = Document.query.filter(Document.case_id.in_(case_ids)).order_by(Document.uploaded_at.desc()).all()
            
            for doc in docs:
                case = HelpCase.query.get(doc.case_id)
                documents.append({
                    'id': doc.id,
                    'filename': doc.filename,
                    'document_type': doc.document_type,
                    'case_id': doc.case_id,
                    'case_title': case.title if case else 'Unknown Case',
                    'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    'verified': doc.verified,
                    'notes': doc.notes,
                    'file_size': doc.file_size or 0
                })
                
        elif user.role == 'admin':
            # Admin can see all documents
            docs = Document.query.order_by(Document.uploaded_at.desc()).all()
            for doc in docs:
                case = HelpCase.query.get(doc.case_id)
                uploader = User.query.get(doc.uploaded_by) if doc.uploaded_by else None
                documents.append({
                    'id': doc.id,
                    'filename': doc.filename,
                    'document_type': doc.document_type,
                    'case_id': doc.case_id,
                    'case_title': case.title if case else 'Unknown Case',
                    'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    'verified': doc.verified,
                    'verified_at': doc.verified_at.isoformat() if doc.verified_at else None,
                    'verified_by': doc.verified_by,
                    'notes': doc.notes,
                    'file_size': doc.file_size or 0,
                    'uploaded_by': uploader.full_name if uploader else 'Unknown'
                })
        
        elif user.role == 'donor':
            # Donors can see non-rejected documents of approved cases
            docs = Document.query.filter(Document.verified.isnot(False)).all()
            for doc in docs:
                case = HelpCase.query.get(doc.case_id)
                if case and case.status in ['approved', 'funded']:
                    documents.append({
                        'id': doc.id,
                        'filename': doc.filename,
                        'document_type': doc.document_type,
                        'case_id': doc.case_id,
                        'case_title': case.title if case else 'Unknown Case',
                        'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                        'verified': doc.verified,
                        'notes': doc.notes,
                        'file_size': doc.file_size or 0
                    })
        
        return jsonify(documents), 200
        
    except Exception as e:
        print(f"Error fetching documents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/case/<int:case_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_case_documents(case_id):
    """Get all documents for a specific case"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get the case
        case = HelpCase.query.get_or_404(case_id)
        
        # Check permissions based on role
        if user.role == 'beneficiary':
            # Beneficiaries can only see their own cases
            beneficiary = Beneficiary.query.filter_by(user_id=user.id).first()
            if not beneficiary or case.beneficiary_id != beneficiary.id:
                return jsonify({'error': 'Unauthorized - You can only view your own cases'}), 403
                
        elif user.role == 'donor':
            # Donors can only see documents of approved cases
            if case.status not in ['approved', 'funded']:
                return jsonify({'error': 'Unauthorized - Case not approved'}), 403
                
        elif user.role == 'admin':
            # Admins can see all documents
            pass
        else:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get documents
        documents = Document.query.filter_by(case_id=case_id).order_by(Document.uploaded_at.desc()).all()
        
        doc_list = []
        for doc in documents:
            # For donors, hide only explicitly rejected documents
            if user.role == 'donor' and doc.verified is False:
                continue
                
            doc_list.append({
                'id': doc.id,
                'filename': doc.filename,
                'document_type': doc.document_type,
                'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                'verified': doc.verified,
                'notes': doc.notes,
                'file_size': doc.file_size or 0,
                'case_id': doc.case_id
            })
        
        return jsonify(doc_list), 200
        
    except Exception as e:
        print(f"Error fetching case documents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<int:document_id>/view', methods=['GET', 'OPTIONS'])
@jwt_required()
def view_document(document_id):
    """View a document"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        document = Document.query.get_or_404(document_id)
        
        # Check if file exists
        if not os.path.exists(document.file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Check permissions based on role
        case = HelpCase.query.get(document.case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        if user.role == 'beneficiary':
            # Beneficiaries can only view their own documents
            beneficiary = Beneficiary.query.filter_by(user_id=user.id).first()
            if not beneficiary or case.beneficiary_id != beneficiary.id:
                return jsonify({'error': 'Unauthorized'}), 403
                
        elif user.role == 'donor':
            # Donors can only view non-rejected documents of approved cases
            if case.status not in ['approved', 'funded']:
                return jsonify({'error': 'Unauthorized - Case not approved'}), 403
            if document.verified is False:
                return jsonify({'error': 'Document rejected'}), 403
                
        elif user.role == 'admin':
            # Admins can view all documents
            pass
        else:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(document.file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        return send_file(
            document.file_path,
            mimetype=mime_type,
            as_attachment=False,
            download_name=document.filename
        )
        
    except Exception as e:
        print(f"Error viewing document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<int:document_id>/download', methods=['GET', 'OPTIONS'])
@jwt_required()
def download_document(document_id):
    """Download a document"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        document = Document.query.get_or_404(document_id)
        
        # Check if file exists
        if not os.path.exists(document.file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Check permissions based on role
        case = HelpCase.query.get(document.case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        if user.role == 'beneficiary':
            # Beneficiaries can only download their own documents
            beneficiary = Beneficiary.query.filter_by(user_id=user.id).first()
            if not beneficiary or case.beneficiary_id != beneficiary.id:
                return jsonify({'error': 'Unauthorized'}), 403
                
        elif user.role == 'donor':
            # Donors can only download non-rejected documents of approved cases
            if case.status not in ['approved', 'funded']:
                return jsonify({'error': 'Unauthorized - Case not approved'}), 403
            if document.verified is False:
                return jsonify({'error': 'Document rejected'}), 403
                
        elif user.role == 'admin':
            # Admins can download all documents
            pass
        else:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.filename
        )
        
    except Exception as e:
        print(f"Error downloading document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<int:document_id>/verify', methods=['POST', 'OPTIONS'])
@jwt_required()
def verify_document(document_id):
    """Admin verifies a document"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        document = Document.query.get_or_404(document_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        verified = data.get('verified', True)
        document.verified = verified
        document.verified_at = datetime.utcnow()
        document.verified_by = user.id
        
        db.session.commit()
        
        status = "verified" if verified else "rejected"
        return jsonify({'message': f'Document {status} successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error verifying document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<int:document_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def delete_document(document_id):
    """Delete a document"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        document = Document.query.get_or_404(document_id)
        
        # Check permissions
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Admin can delete any document
        if user.role == 'admin':
            pass  # Allow
        # Beneficiary can delete their own documents
        elif user.role == 'beneficiary':
            beneficiary = Beneficiary.query.filter_by(user_id=user.id).first()
            case = HelpCase.query.get(document.case_id)
            if not beneficiary or case.beneficiary_id != beneficiary.id:
                return jsonify({'error': 'Unauthorized'}), 403
        else:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Delete file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500