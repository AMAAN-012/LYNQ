import sys
print("=" * 60)
print("DEBUGGING ENVIRONMENT")
print("=" * 60)

print(f"\nPython: {sys.version}")
print(f"\nPython Location: {sys.executable}")

try:
    import flask_sqlalchemy
    print(f"\n✅ Flask-SQLAlchemy: {flask_sqlalchemy.__version__}")
    print(f"   Location: {flask_sqlalchemy.__file__}")
except Exception as e:
    print(f"\n❌ Flask-SQLAlchemy Error: {e}")

try:
    import sqlalchemy
    print(f"\n✅ SQLAlchemy: {sqlalchemy.__version__}")
    print(f"   Location: {sqlalchemy.__file__}")
    
    # Check if db.Column exists
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
    print(f"\n✅ db.Column exists: {hasattr(db, 'Column')}")
except Exception as e:
    print(f"\n❌ SQLAlchemy Error: {e}")

print("\n" + "=" * 60)