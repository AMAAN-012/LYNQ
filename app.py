import os
from dotenv import load_dotenv
from flask import Flask, request, session, redirect, url_for

load_dotenv()

def create_app(config_name=None):
    """Application factory"""
    from config import get_config
    from models import db
    
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load configuration
    cfg = get_config(config_name)
    app.config.from_object(cfg)
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        # Import models AFTER db initialization
        from models.user import User
        from models.job import Job
        from models.application import Application
        from models.post import Post
        from models.comment import Comment
        from models.skill import Skill
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created/verified")
        
        # Only check/create admin if table exists and has data
        try:
            admin = User.query.filter_by(usertag='admin').first()
            if not admin:
                admin = User(
                    email='admin@lynqplat.com',
                    full_name='Admin User',
                    usertag='admin',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created")
                print("   Email: admin@lynqplat.com")
                print("   Password: admin123")
            else:
                print("✅ Admin user already exists")
        except Exception as e:
            print(f"⚠️  Could not check admin user: {e}")
            print("   This is normal on first run with fresh database")
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.jobs import jobs_bp
    from routes.community import community_bp
    from routes.user_profile import user_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(user_bp)
    
    # Root route
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.home'))
        return redirect(url_for('auth.login'))
    
    # Middleware: Check login before every request
    @app.before_request
    def require_login():
        allowed_endpoints = ('auth.login', 'auth.register', 'static')
        if request.endpoint and request.endpoint not in allowed_endpoints and 'user_id' not in session:
            return redirect(url_for('auth.login'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*60)
    print("🚀 Job Platform is starting...")
    print("📍 Visit: http://localhost:5000")
    print("📧 Admin Email: admin@lynqplat.com")
    print("🔐 Admin Password: admin123")
    print("="*60 + "\n")
    app.run(debug=True, host='localhost', port=5000)