# Employee Login Monitoring System

## Overview
Employee Login Monitoring System is a Flask-based web application that monitors employee login activities and detects suspicious login behavior using Machine Learning.

## Features
- Employee Registration
- Secure Login using Bcrypt
- Account Lock after 3 Failed Attempts
- Login History
- Failed Login Monitoring
- Admin Dashboard
- Risk Level Detection
- Machine Learning Based Login Risk Prediction
- Interactive Charts using Chart.js
- SQLite Database

## Technologies Used
- Python
- Flask
- SQLite
- SQLAlchemy
- HTML
- CSS
- Bootstrap
- JavaScript
- Chart.js
- Scikit-learn
- Pandas

## Machine Learning
The project uses a Decision Tree Classifier trained on a login dataset to predict:
- Low Risk
- Medium Risk
- High Risk

## Installation

```bash
pip install -r requirements.txt
python app.py
```

## Project Structure

```
Employee_Login_Monitoring_System
│
├── dataset
├── ml
├── models
├── routes
├── static
├── templates
├── app.py
├── config.py
└── requirements.txt
```

## Author

Talluru Jahnavi
