from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

STATUS_TRANSLATIONS = {
    'New': 'Новая',
    'Assigned': 'Назначена',
    'In Progress': 'В работе',
    'Completed': 'Выполнена', 
    'Denied': 'Отклонена'
}

class User(db.Model):
    # ... (Остальной код класса User остается прежним) ...
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='worker') # worker, dispatcher, master
    shop_id = db.Column(db.Integer, nullable=True)
    telegram_id = db.Column(db.String(50), nullable=True)

    # Relationships
    requests = db.relationship('Request', backref='author', foreign_keys='Request.user_id')
    assigned_requests = db.relationship('Request', backref='technician', foreign_keys='Request.technician_id')

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "shop_id": self.shop_id
        }

class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)
    # Статус по умолчанию — 'New'
    status = db.Column(db.String(20), default='New') # New, Assigned, In Progress, Completed, Denied
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    device_id = db.Column(db.Integer, nullable=True) # Optional for now

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "photo_path": self.photo_path,
            "status": STATUS_TRANSLATIONS.get(self.status, self.status), 
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "technician_id": self.technician_id,
            "technician_name": self.technician.full_name if self.technician else None,
            "author_name": self.author.full_name if self.author else None
        }

class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    shop_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "shop_id": self.shop_id
        }