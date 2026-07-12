from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.String(20), unique=True, nullable=False)

    full_name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default="Employee")

    failed_attempts = db.Column(db.Integer, default=0)

    locked_until = db.Column(db.DateTime, nullable=True)
    last_browser = db.Column(db.String(100))

    last_operating_system = db.Column(db.String(100))

    last_device = db.Column(db.String(100))

    def __repr__(self):
        return f"<User {self.full_name}>"