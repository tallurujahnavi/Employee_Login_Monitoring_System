from models.user import User
from werkzeug.security import generate_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
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

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Create database tables
with app.app_context():
    db.create_all()

    # Create default admin if database is empty
    admin = User.query.filter_by(email="jahnavi@gmail.com").first()

    if not admin:
        admin = User(
            employee_id="EMP001",
            full_name="Talluru Jahnavi",
            email="jahnavi@gmail.com",
            password=bcrypt.generate_password_hash("admin123").decode("utf-8"),
            role="Admin"
        )

        db.session.add(admin)
        db.session.commit()

        print("✅ Default admin created!")

    # Display users in database
    users = User.query.all()
    print("Users in database:", users)

    for u in users:
        print(u.id, u.employee_id, u.email, u.role)


# ==========================
# FLASK LOGIN
# ==========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# ==========================
# LOGIN
# ==========================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")
        print("Email entered:", email)
        print("Searching for:", repr(email))

        users = User.query.all()
        print("All emails:", [u.email for u in users])
        user = User.query.filter_by(email=email.strip()).first()

        print("Found:", user)
        print("User found:", user)
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

                # Login the user
                login_user(user)

                # Redirect based on role
                if user.role == "Admin":
                    return redirect(url_for("admin"))
                else:
                    return redirect(url_for("dashboard"))
                

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
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        user=current_user
    )

# ==========================
# LOGIN HISTORY
# ==========================

@app.route("/history")
@login_required
def history():

    if current_user.role != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))

    logs = LoginLog.query.order_by(
        LoginLog.login_time.desc()
    ).all()

    return render_template(
        "login_history.html",
        logs=logs
    )
# ==========================
# FAILED LOGIN HISTORY
# ==========================

@app.route("/failed-logins")
@login_required
def failed_logins():

    if current_user.role != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))

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
@login_required
def admin():

    if current_user.role != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))

    # User Statistics
    total_users = User.query.count()
    total_employees = User.query.filter_by(role="Employee").count()
    total_admins = User.query.filter_by(role="Admin").count()

    employees = User.query.order_by(User.id.desc()).all()

    # Login Statistics
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
        total_employees=total_employees,
        total_admins=total_admins,

        total_logins=total_logins,
        success=success,
        failed=failed,

        low=low,
        medium=medium,
        high=high,

        logs=logs,
        employees=employees
    )
    # ==========================
    # USER STATISTICS
    # ==========================
    total_users = User.query.count()

    total_employees = User.query.filter_by(role="Employee").count()

    total_admins = User.query.filter_by(role="Admin").count()

    # Get all registered employees
    employees = User.query.order_by(User.id.desc()).all()

    # ==========================
    # LOGIN STATISTICS
    # ==========================
    total_logins = LoginLog.query.count()

    success = LoginLog.query.filter_by(status="Success").count()

    failed = FailedLogin.query.count()

    # ==========================
    # ML RISK STATISTICS
    # ==========================
    low = LoginLog.query.filter_by(risk_level="Low").count()

    medium = LoginLog.query.filter_by(risk_level="Medium").count()

    high = LoginLog.query.filter_by(risk_level="High").count()

    # ==========================
    # RECENT LOGIN LOGS
    # ==========================
    logs = LoginLog.query.order_by(
        LoginLog.login_time.desc()
    ).limit(100).all()

    return render_template(
        "admin_dashboard.html",

        total_users=total_users,
        total_employees=total_employees,
        total_admins=total_admins,

        total_logins=total_logins,
        success=success,
        failed=failed,

        low=low,
        medium=medium,
        high=high,

        logs=logs,

        employees=employees
    )


# ==========================
# VIEW EMPLOYEES
# ==========================
@app.route("/employees")
@login_required
def employees():

    if current_user.role != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))

    users = User.query.order_by(User.id).all()

    return render_template(
        "employees.html",
        users=users
    )

    
# ==========================
# EDIT EMPLOYEE
# ==========================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_employee(id):

    if current_user.role != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for("dashboard"))


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
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# ==========================
# RUN APP
# ==========================

if __name__ == "__main__":
    app.run(debug=True)