from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    full_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="Employee"
    )

    failed_attempts = db.Column(
        db.Integer,
        default=0
    )

    locked_until = db.Column(
        db.DateTime,
        nullable=True
    )

    last_browser = db.Column(
        db.String(100),
        nullable=True
    )

    last_operating_system = db.Column(
        db.String(100),
        nullable=True
    )

    last_device = db.Column(
        db.String(100),
        nullable=True
    )

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return (
            f"<User(id={self.id}, "
            f"employee_id='{self.employee_id}', "
            f"email='{self.email}', "
            f"role='{self.role}')>"
        )