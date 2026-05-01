# backend/app.py
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
import os
import logging
from myproject.extensions import db, bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    allowed_origins = [
        'http://127.0.0.1:3000',
        'http://127.0.0.1:3003',
        'http://localhost:3000',
        'http://localhost:3003',
        'http://127.0.0.1:5500',
        'http://localhost:5500',
        'http://127.0.0.1:5501',
        'http://localhost:5501',
        'null',  # file:// origin used by browsers opening HTML directly
    ]
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    CORS(
        app,
        resources={r'/api/*': {'origins': allowed_origins}},
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    )

    from routes.documents import documents_bp
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    # Register blueprints with error handling
    try:
        from routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        logger.info("Auth blueprint registered")
    except Exception as e:
        import traceback
        logger.error(f"Failed to register auth blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from routes.cases import cases_bp
        app.register_blueprint(cases_bp, url_prefix='/api/cases')
        logger.info("Cases blueprint registered")
    except Exception as e:
        import traceback
        logger.error(f"Failed to register cases blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from routes.donations import donations_bp
        app.register_blueprint(donations_bp, url_prefix='/api/donations')
        logger.info("Donations blueprint registered")
    except Exception as e:
        import traceback
        logger.error(f"Failed to register donations blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        logger.info("Admin blueprint registered")
    except Exception as e:
        import traceback
        logger.error(f"Failed to register admin blueprint: {e}")
        logger.error(traceback.format_exc())

    @app.route('/api/debug/routes')
    def debug_routes():
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        return jsonify(sorted(routes))
    
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Smart Donation Platform API is running'})
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created")
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('BACKEND_PORT', '5001')))
