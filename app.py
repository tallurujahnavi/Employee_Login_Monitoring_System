from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from utils.device_detector import get_device_details
from datetime import datetime, timedelta
from config import Config
from models.user import db, User
from models.login_log import LoginLog
from models.failed_login import FailedLogin
from ml.predict import predict_risk

# ==========================
# CREATE FLASK APP
# ==========================

app = Flask(__name__)
app.secret_key = "employee_login_monitoring_system"

# Load configuration
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)

# Create database tables
with app.app_context():
    db.create_all()

# ==========================
# LOGIN
# ==========================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        # Detect browser, OS and device
        user_agent = request.headers.get("User-Agent")
        browser, operating_system, device = get_device_details(user_agent)

        # -----------------------------
        # USER EXISTS
        # -----------------------------
        if user:

            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():

                remaining = int(
                    (user.locked_until - datetime.utcnow()).total_seconds() / 60
                ) + 1

                flash(
                    f"Account locked. Try again in {remaining} minute(s).",
                    "danger"
                )

                return redirect(url_for("login"))

            # -----------------------------
            # CORRECT PASSWORD
            # -----------------------------
            if bcrypt.check_password_hash(user.password, password):

                # Reset failed attempts
                user.failed_attempts = 0
                user.locked_until = None

                # -----------------------------
                # MACHINE LEARNING RISK PREDICTION
                # -----------------------------
                current_hour = datetime.now().hour

                new_browser = 1 if (
                    user.last_browser and user.last_browser != browser
                ) else 0

                new_device = 1 if (
                    user.last_device and user.last_device != device
                ) else 0

                # Skip IP if not available
                new_ip = 0

                # Weekend
                weekend = 1 if datetime.now().weekday() >= 5 else 0

                # Predict risk using ML model
                risk = predict_risk(
                    current_hour,
                    user.failed_attempts,
                    new_device,
                    new_browser,
                    new_ip,
                    weekend
                )

                # Save latest login details
                user.last_browser = browser
                user.last_operating_system = operating_system
                user.last_device = device

                # Save login history
                login_log = LoginLog(
                    employee_id=user.employee_id,
                    full_name=user.full_name,
                    email=user.email,
                    ip_address=request.remote_addr,
                    browser=browser,
                    operating_system=operating_system,
                    device=device,
                    user_agent=user_agent,
                    status="Success",
                    risk_level=risk
                )

                db.session.add(login_log)
                db.session.commit()

                return render_template(
                    "dashboard.html",
                    user=user
                )

            # -----------------------------
            # WRONG PASSWORD
            # -----------------------------
            else:

                user.failed_attempts += 1

                failed = FailedLogin(
                    email=email,
                    ip_address=request.remote_addr,
                    browser=browser,
                    operating_system=operating_system,
                    device=device,
                    user_agent=user_agent,
                    reason="Wrong Password"
                )

                db.session.add(failed)

                if user.failed_attempts >= 3:

                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)

                    db.session.commit()

                    flash(
                        "Your account has been locked for 15 minutes after 3 failed login attempts.",
                        "danger"
                    )

                    return redirect(url_for("login"))

                db.session.commit()

                flash(
                    f"Incorrect Password! Attempt {user.failed_attempts}/3",
                    "danger"
                )

                return redirect(url_for("login"))

        # -----------------------------
        # USER NOT FOUND
        # -----------------------------
        else:

            failed = FailedLogin(
                email=email,
                ip_address=request.remote_addr,
                browser=browser,
                operating_system=operating_system,
                device=device,
                user_agent=user_agent,
                reason="User Not Found"
            )

            db.session.add(failed)
            db.session.commit()

            flash("User not found!", "warning")

            return redirect(url_for("login"))

    return render_template("login.html")

# ==========================
# REGISTER
# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        employee_id = request.form.get("employee_id")
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already exists!", "warning")
            return redirect(url_for("register"))

        # Encrypt password
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Create new employee
        new_user = User(
            employee_id=employee_id,
            full_name=full_name,
            email=email,
            password=hashed_password,
            role="Employee"
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# ==========================
# EMPLOYEE DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ==========================
# LOGIN HISTORY
# ==========================

@app.route("/history")
def history():

    logs = LoginLog.query.order_by(LoginLog.login_time.desc()).all()

    return render_template(
        "login_history.html",
        logs=logs
    )
# ==========================
# FAILED LOGIN HISTORY
# ==========================

@app.route("/failed-logins")
def failed_logins():

    logs = FailedLogin.query.order_by(
        FailedLogin.login_time.desc()
    ).all()

    return render_template(
        "failed_logins.html",
        logs=logs
    )
# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route("/admin")
def admin():

    total_users = User.query.count()

    total_logins = LoginLog.query.count()

    success = LoginLog.query.filter_by(status="Success").count()

    failed = FailedLogin.query.count()

    # ML Risk Statistics
    low = LoginLog.query.filter_by(risk_level="Low").count()

    medium = LoginLog.query.filter_by(risk_level="Medium").count()

    high = LoginLog.query.filter_by(risk_level="High").count()

    logs = LoginLog.query.order_by(
        LoginLog.login_time.desc()
    ).limit(100).all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_logins=total_logins,
        success=success,
        failed=failed,
        low=low,
        medium=medium,
        high=high,
        logs=logs
    )


# ==========================
# VIEW EMPLOYEES
# ==========================

@app.route("/employees")
def employees():

    users = User.query.order_by(User.id).all()

    return render_template(
        "employees.html",
        users=users
    )
# ==========================
# EDIT EMPLOYEE
# ==========================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_employee(id):

    user = User.query.get_or_404(id)

    if request.method == "POST":

        user.employee_id = request.form.get("employee_id")
        user.full_name = request.form.get("full_name")
        user.email = request.form.get("email")
        user.role = request.form.get("role")

        db.session.commit()

        return redirect(url_for("employees"))

    return render_template(
        "edit_employee.html",
        user=user
    )


@app.route("/delete/<int:id>")
def delete_employee(id):

    user = User.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("employees"))
# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():
    return redirect(url_for("login"))


# ==========================
# RUN APP
# ==========================

if __name__ == "__main__":
    app.run(debug=True)