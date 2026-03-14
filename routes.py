from flask import request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, Flos, Group, GroupMember, Message, GroupMessage
from mail_service import mail_service
import uuid
import hashlib
import jwt
import random
import string
from config import Config

jwt = JWTManager()

def register_routes(app):
    jwt.init_app(app)
    
    @app.route('/api/test', methods=['GET'])
    def test():
        return jsonify({'message': 'Test route works'}), 200
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.get_json()
        if not data or not 'Username' in data or not 'Password' in data or not 'Email' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        
        if User.query.filter_by(Username=data['Username']).first():
            return jsonify({'message': 'Username already exists'}), 400
        
        if User.query.filter_by(Email=data['Email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        # Generate verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # Send verification email
        email_sent = mail_service.send_verification_email(data['Email'], verification_code)
        if not email_sent:
            print(f"Warning: Email sending skipped (SMTP credentials not set). Verification code for {data['Username']}: {verification_code}")
            # 在开发环境中，允许跳过邮件发送
            pass
        
        hashed_password = hashlib.sha256(data['Password'].encode()).hexdigest()
        new_user = User(
            CID=str(uuid.uuid4()),
            Username=data['Username'],
            Email=data['Email'],
            Password=hashed_password,
            verification_code=verification_code
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Verification email sent. Please check your email to verify.', 'CID': new_user.CID}), 201
    
    @app.route('/api/auth/verify', methods=['POST'])
    def verify():
        data = request.get_json()
        if not data or not 'CID' in data or not 'verification_code' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        
        user = User.query.filter_by(CID=data['CID']).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if user.verified:
            return jsonify({'message': 'User already verified'}), 400
        
        if user.verification_code != data['verification_code']:
            return jsonify({'message': 'Invalid verification code'}), 401
        
        user.verified = True
        user.verification_code = None
        db.session.commit()
        
        return jsonify({'message': 'Verification successful'}), 200
    
    @app.route('/api/auth/resend', methods=['POST'])
    def resend_verification():
        data = request.get_json()
        if not data or not 'CID' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        
        user = User.query.filter_by(CID=data['CID']).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if user.verified:
            return jsonify({'message': 'User already verified'}), 400
        
        # Generate new verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # Send verification email
        if not mail_service.send_verification_email(user.Email, verification_code):
            return jsonify({'message': 'Failed to send verification email'}), 500
        
        user.verification_code = verification_code
        db.session.commit()
        
        return jsonify({'message': 'Verification email resent. Please check your email.'}), 200
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        if not data or not 'Username' in data or not 'Password' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        
        user = User.query.filter_by(Username=data['Username']).first()
        if not user or not check_password_hash(user.Password, data['Password']):
            return jsonify({'message': 'Invalid username or password'}), 401
        
        if not user.verified:
            return jsonify({'message': 'Please verify your email first'}), 403
        
        access_token = create_access_token(identity=user.CID)
        return jsonify({'access_token': access_token, 'CID': user.CID, 'Username': user.Username}), 200
    
    @app.route('/api/users', methods=['GET'])
    @jwt_required()
    def get_users():
        users = User.query.all()
        return jsonify([{
            'CID': user.CID,
            'Username': user.Username,
            'Flos': user.Flos
        } for user in users]), 200
    
    @app.route('/api/messages', methods=['POST'])
    @jwt_required()
    def send_message():
        data = request.get_json()
        if not data or not 'receiver_id' in data or not 'content' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        
        sender_id = get_jwt_identity()
        new_message = Message(
            sender_id=sender_id,
            receiver_id=data['receiver_id'],
            content=data['content']
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({'message': 'Message sent successfully'}), 201
    
    @app.route('/api/messages/<receiver_id>', methods=['GET'])
    @jwt_required()
    def get_messages(receiver_id):
        sender_id = get_jwt_identity()
        messages = Message.query.filter(
            ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
        ).order_by(Message.sent_at).all()
        
        return jsonify([{
            'id': message.id,
            'sender_id': message.sender_id,
            'receiver_id': message.receiver_id,
            'content': message.content,
            'sent_at': message.sent_at
        } for message in messages]), 200
    
    @app.route('/api/groups', methods=['POST'])
    @jwt_required()
    def create_group():
        data = request.get_json()
        if not data or not 'name' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        
        creator_id = get_jwt_identity()
        new_group = Group(
            name=data['name'],
            created_by=creator_id
        )
        
        db.session.add(new_group)
        db.session.commit()
        
        # Add creator as member
        new_member = GroupMember(
            group_id=new_group.id,
            CID=creator_id
        )
        db.session.add(new_member)
        db.session.commit()
        
        return jsonify({'message': 'Group created successfully', 'group_id': new_group.id}), 201
    
    @app.route('/api/groups', methods=['GET'])
    @jwt_required()
    def get_groups():
        user_id = get_jwt_identity()
        memberships = GroupMember.query.filter_by(CID=user_id).all()
        groups = [Group.query.get(m.group_id) for m in memberships]
        
        return jsonify([{
            'id': group.id,
            'name': group.name,
            'created_by': group.created_by
        } for group in groups]), 200
    
    @app.route('/api/groups/<group_id>/members', methods=['POST'])
    @jwt_required()
    def add_group_member(group_id):
        data = request.get_json()
        if not data or not 'CID' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        
        # Check if user is group member
        user_id = get_jwt_identity()
        if not GroupMember.query.filter_by(group_id=group_id, CID=user_id).first():
            return jsonify({'message': 'You are not a member of this group'}), 403
        
        # Check if user already in group
        if GroupMember.query.filter_by(group_id=group_id, CID=data['CID']).first():
            return jsonify({'message': 'User already in group'}), 400
        
        new_member = GroupMember(
            group_id=group_id,
            CID=data['CID']
        )
        
        db.session.add(new_member)
        db.session.commit()
        
        return jsonify({'message': 'Member added successfully'}), 201
    
    @app.route('/api/groups/<group_id>/messages', methods=['POST'])
    @jwt_required()
    def send_group_message(group_id):
        data = request.get_json()
        if not data or not 'content' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        
        # Check if user is group member
        user_id = get_jwt_identity()
        if not GroupMember.query.filter_by(group_id=group_id, CID=user_id).first():
            return jsonify({'message': 'You are not a member of this group'}), 403
        
        new_message = GroupMessage(
            group_id=group_id,
            sender_id=user_id,
            content=data['content']
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({'message': 'Message sent successfully'}), 201
    
    @app.route('/api/groups/<group_id>/messages', methods=['GET'])
    @jwt_required()
    def get_group_messages(group_id):
        # Check if user is group member
        user_id = get_jwt_identity()
        if not GroupMember.query.filter_by(group_id=group_id, CID=user_id).first():
            return jsonify({'message': 'You are not a member of this group'}), 403
        
        messages = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.sent_at).all()
        
        return jsonify([{
            'id': message.id,
            'sender_id': message.sender_id,
            'content': message.content,
            'sent_at': message.sent_at
        } for message in messages]), 200
    
    @app.route('/api/online', methods=['POST'])
    @jwt_required()
    def set_online():
        data = request.get_json()
        if not data or not 'CFD' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        
        user_id = get_jwt_identity()
        # Generate Kiryu (JWT token)
        kiryu = jwt.encode({'CID': user_id, 'CFD': data['CFD']}, Config.JWT_SECRET_KEY, algorithm='HS256')
        
        # Check if already online
        existing = Flos.query.filter_by(CID=user_id).first()
        if existing:
            existing.Kiryu = kiryu
            existing.CFD = data['CFD']
        else:
            new_flos = Flos(
                Kiryu=kiryu,
                CID=user_id,
                CFD=data['CFD']
            )
            db.session.add(new_flos)
        
        db.session.commit()
        
        return jsonify({'message': 'Online status set successfully', 'Kiryu': kiryu}), 200
    
    @app.route('/api/online', methods=['GET'])
    @jwt_required()
    def get_online_users():
        online_users = Flos.query.all()
        return jsonify([{
            'CID': user.CID,
            'CFD': user.CFD
        } for user in online_users]), 200

def check_password_hash(hashed_password, password):
    return hashed_password == hashlib.sha256(password.encode()).hexdigest()