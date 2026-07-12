import joblib

# Load the trained model
model = joblib.load("ml/model.pkl")

def predict_risk(
    login_hour,
    failed_attempts,
    new_device,
    new_browser,
    new_ip,
    weekend
):

    prediction = model.predict([[
        login_hour,
        failed_attempts,
        new_device,
        new_browser,
        new_ip,
        weekend
    ]])

    return prediction[0]