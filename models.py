from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    CID = db.Column(db.String(36), primary_key=True, unique=True, nullable=False)
    Username = db.Column(db.String(50), unique=True, nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Stos = db.Column(db.Boolean, default=False)
    Flos = db.Column(db.String(100), default='在线')
    Password = db.Column(db.String(100), nullable=False)
    verification_code = db.Column(db.String(6), nullable=True)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Flos(db.Model):
    __tablename__ = 'flos'
    id = db.Column(db.Integer, primary_key=True)
    Kiryu = db.Column(db.String(255), nullable=False)
    CID = db.Column(db.String(36), db.ForeignKey('users.CID'), nullable=False)
    CFD = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.String(36), db.ForeignKey('users.CID'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    CID = db.Column(db.String(36), db.ForeignKey('users.CID'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.CID'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('users.CID'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupMessage(db.Model):
    __tablename__ = 'group_messages'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.CID'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)