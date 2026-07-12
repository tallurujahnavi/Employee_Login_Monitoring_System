from datetime import datetime
from models.user import db


class LoginLog(db.Model):

    __tablename__ = "login_logs"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.String(20))
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))

    login_time = db.Column(db.DateTime, default=datetime.utcnow)

    ip_address = db.Column(db.String(100))

    browser = db.Column(db.String(100))

    operating_system = db.Column(db.String(100))

    device = db.Column(db.String(100))

    user_agent = db.Column(db.Text)

    status = db.Column(db.String(20))

    risk_level = db.Column(db.String(20), default="Low")