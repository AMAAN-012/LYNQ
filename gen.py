from app import create_app
from models import db
from models.application import Application

app = create_app()
with app.app_context():
    apps = Application.query.all()
    for a in apps:
        print(f"ID: {a.id}, User: {a.user_id}, Job: {a.job_id}, Status: '{a.status}'")