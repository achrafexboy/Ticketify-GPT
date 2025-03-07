from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)  # ✅ Email for login
    username = db.Column(db.String(50), unique=True, nullable=False)  # ✅ Separate username
    password_hash = db.Column(db.String(128), nullable=False)
    poste = db.Column(db.String(20), nullable=False)  # ✅ New Role Field (Dev, PM, QA, Client)
    email_notifications = db.Column(db.Boolean, default=True)  # Default: Enabled

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to User
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
