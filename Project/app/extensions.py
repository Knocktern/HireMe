from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_socketio import SocketIO

db = SQLAlchemy()
mail = Mail()
socketio = SocketIO(cors_allowed_origins="*")
