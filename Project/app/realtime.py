from flask_socketio import emit, join_room, leave_room
from flask import session, request
from datetime import datetime
from extensions import db, socketio
from models import User, InterviewParticipant
from collections import defaultdict

# Track interview participants
INTERVIEW_PARTICIPANTS = defaultdict(dict)  # room_id -> { sid: user_info }
SID_TO_INTERVIEW_ROOM = {}  # sid -> room_id

@socketio.on('join_interview')
def on_join_interview(data):
    room_id = str(data['room'])
    room_code = data['room_code']
    user_role = data['role']
    join_room(room_id)
    
    # Get user info from session
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        user_info = {
            'username': f"{user.first_name} {user.last_name}",
            'role': user_role,
            'user_id': user.id
        }
        
        # Track participant
        INTERVIEW_PARTICIPANTS[room_id][request.sid] = user_info
        SID_TO_INTERVIEW_ROOM[request.sid] = room_id
        
        # Update participant status in database
        participant = InterviewParticipant.query.filter_by(
            room_id=int(room_id),
            user_id=user.id
        ).first()
        if participant:
            participant.joined_at = datetime.utcnow()
            participant.is_active = True
            db.session.commit()
        
        # Send existing participants to the joiner
        others = [
            {'sid': sid, 'username': info['username'], 'role': info['role']}
            for sid, info in INTERVIEW_PARTICIPANTS[room_id].items()
            if sid != request.sid
        ]
        emit('participants', {'participants': others}, to=request.sid)
        
        # Notify others in room
        emit('user_joined', {
            'sid': request.sid,
            'username': user_info['username'],
            'role': user_info['role']
        }, room=room_id, include_self=False)

@socketio.on('leave_interview')
def on_leave_interview(data):
    room_id = str(data['room'])
    leave_room(room_id)
    
    # Cleanup tracking
    user_info = INTERVIEW_PARTICIPANTS[room_id].pop(request.sid, None)
    SID_TO_INTERVIEW_ROOM.pop(request.sid, None)
    
    if user_info and 'user_id' in session:
        # Update participant status in database
        participant = InterviewParticipant.query.filter_by(
            room_id=int(room_id), 
            user_id=user_info['user_id']
        ).first()
        if participant:
            participant.left_at = datetime.utcnow()
            participant.is_active = False
            db.session.commit()
    
    emit('user_left', {
        'sid': request.sid, 
        'username': user_info['username'] if user_info else 'Unknown'
    }, room=room_id)

@socketio.on('disconnect')
def on_interview_disconnect():
    sid = request.sid
    room_id = SID_TO_INTERVIEW_ROOM.pop(sid, None)
    
    if room_id:
        user_info = INTERVIEW_PARTICIPANTS[room_id].pop(sid, None)
        
        if user_info:
            emit('user_left', {
                'sid': sid, 
                'username': user_info['username']
            }, room=room_id)

# WebRTC Signaling Events
@socketio.on('offer')
def on_interview_offer(data):
    to_sid = data.get('to')
    if not to_sid:
        return
    emit('offer', {
        'offer': data['offer'],
        'from': request.sid
    }, to=to_sid)

@socketio.on('answer')
def on_interview_answer(data):
    to_sid = data.get('to')
    if not to_sid:
        return
    emit('answer', {
        'answer': data['answer'],
        'from': request.sid
    }, to=to_sid)

@socketio.on('ice_candidate')
def on_interview_ice_candidate(data):
    to_sid = data.get('to')
    if not to_sid:
        return
    emit('ice_candidate', {
        'candidate': data['candidate'],
        'from': request.sid
    }, to=to_sid)

# Code Editor Events
@socketio.on('code_change')
def on_code_change(data):
    room_id = str(data['room'])
    emit('code_updated', {
        'code': data['code'],
        'language': data.get('language', 'javascript'),
        'from': request.sid
    }, room=room_id, include_self=False)
