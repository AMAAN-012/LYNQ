import os
from app import create_app
from models import db

def reset_database():
    """Drop all tables and recreate them"""
    app = create_app()
    
    with app.app_context():
        print("🗑️  Dropping all tables...")
        db.drop_all()
        print("✅ All tables dropped")
        
        print("🔄 Creating all tables...")
        db.create_all()
        print("✅ All tables created")
        
        # Create admin user
        from models.user import User
        admin = User(
            email='admin@lynqplat.com',
            full_name='Admin User',
            usertag='admin',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ DATABASE RESET SUCCESSFULLY!")
        print("="*60)
        print("📧 Admin Email: admin@lynqplat.com")
        print("🔐 Admin Password: admin123")
        print("="*60 + "\n")

if __name__ == '__main__':
    reset_database()