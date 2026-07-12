import pandas as pd
from datetime import datetime, timedelta
import random

from app import app
from models.user import db
from models.login_log import LoginLog

with app.app_context():

    df = pd.read_csv("dataset/login_dataset.csv")

    LoginLog.query.delete()

    db.session.commit()

    for index, row in df.iterrows():

        login = LoginLog(

            employee_id=f"EMP{random.randint(1000,9999)}",

            full_name=f"Employee {random.randint(1,500)}",

            email=f"user{random.randint(1,500)}@company.com",

            login_time=datetime.now() - timedelta(days=random.randint(0,30)),

            ip_address=f"192.168.1.{random.randint(1,255)}",

            browser=random.choice([
                "Chrome",
                "Edge",
                "Firefox",
                "Safari"
            ]),

            operating_system=random.choice([
                "Windows",
                "Linux",
                "macOS"
            ]),

            device=random.choice([
                "Desktop",
                "Laptop",
                "Mobile"
            ]),

            user_agent="Synthetic Dataset",

            status="Success",

            risk_level=row["Risk_Level"]

        )

        db.session.add(login)

    db.session.commit()

print("Dataset Imported Successfully!")