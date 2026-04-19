import os
import joblib
import pandas as pd

from utils.preprocess import create_features


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model")

MODEL_PATH = os.path.join(MODEL_DIR, "final_sms_classifier_production.joblib")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.joblib")


class SpamPredictor:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.encoder = joblib.load(ENCODER_PATH)
        self.metadata = joblib.load(METADATA_PATH)
        self.feature_columns = self.metadata["feature_columns"]

    def predict(self, message: str) -> dict:
        input_df = pd.DataFrame([{"message": message}])
        featured_df = create_features(input_df)
        input_x = featured_df[self.feature_columns]

        pred_idx = self.model.predict(input_x)[0]
        pred_label = self.encoder.inverse_transform([pred_idx])[0]

        probabilities = self.model.predict_proba(input_x)[0]
        confidence = float(max(probabilities))

        return {
            "message": message,
            "prediction": pred_label,
            "confidence": round(confidence * 100, 2),
            "probabilities": {
                self.encoder.classes_[i]: round(float(probabilities[i]) * 100, 2)
                for i in range(len(self.encoder.classes_))
            },
            "processed_message": featured_df.iloc[0]["processed_message"]
        }


predictor = SpamPredictor()