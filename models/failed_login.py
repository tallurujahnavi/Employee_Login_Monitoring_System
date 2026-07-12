from datetime import datetime
from models.user import db


class FailedLogin(db.Model):

    __tablename__ = "failed_logins"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(100))

    ip_address = db.Column(db.String(100))

    browser = db.Column(db.String(100))

    operating_system = db.Column(db.String(100))

    device = db.Column(db.String(100))

    user_agent = db.Column(db.Text)

    login_time = db.Column(db.DateTime, default=datetime.utcnow)

    reason = db.Column(db.String(100))