import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load dataset
data = pd.read_csv("dataset/login_dataset.csv")

# Features
X = data[
    [
        "Login_Hour",
        "Failed_Attempts",
        "New_Device",
        "New_Browser",
        "New_IP",
        "Weekend"
    ]
]

# Target
y = data["Risk_Level"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Train Random Forest model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print(f"Model Accuracy: {accuracy:.2f}")

# Save model
joblib.dump(model, "ml/model.pkl")

print("Model saved successfully!")