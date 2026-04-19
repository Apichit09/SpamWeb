import os
import joblib
import pandas as pd
import numpy as np

from lime.lime_text import LimeTextExplainer

from utils.preprocess import create_features, text_process


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

        # ให้ LIME แยกคำตาม space เพราะเราจะส่ง processed text ที่ตัดคำแล้วเข้าไป
        self.explainer = LimeTextExplainer(
            class_names=list(self.encoder.classes_),
            split_expression=r"\s+",
            bow=True
        )

    def predict(self, message: str) -> dict:
        input_df = pd.DataFrame([{"message": message}])
        featured_df = create_features(input_df)
        input_x = featured_df[self.feature_columns]

        pred_idx = self.model.predict(input_x)[0]
        pred_label = self.encoder.inverse_transform([pred_idx])[0]

        probabilities = self.model.predict_proba(input_x)[0]
        confidence = round(float(np.max(probabilities)) * 100, 2)

        return {
            "message": message,
            "prediction": pred_label,
            "confidence": confidence,
            "probabilities": {
                self.encoder.classes_[i]: round(float(probabilities[i]) * 100, 2)
                for i in range(len(self.encoder.classes_))
            },
            "processed_message": featured_df.iloc[0]["processed_message"]
        }

    def _lime_predict_proba_processed(self, processed_texts):
        """
        LIME จะส่งข้อความที่ตัดคำแล้ว (processed text) เข้ามาหลายข้อความ
        เราจะสร้าง feature ใหม่ แล้วบังคับให้ processed_message ใช้ค่าจาก LIME โดยตรง
        เพื่อให้ token ที่อธิบายตรงกับ token ที่โมเดลใช้
        """
        rows = []

        for processed_text in processed_texts:
            # สร้าง DataFrame ชั่วคราว
            temp_df = pd.DataFrame([{"message": processed_text}])

            # สร้าง feature ตามระบบเดิม
            featured_df = create_features(temp_df)

            # บังคับให้คอลัมน์ processed_message ใช้ค่าที่ LIME ส่งเข้ามาโดยตรง
            # เพื่อไม่ให้เกิดการตัดคำซ้ำแล้วแตกเป็นเศษคำ
            featured_df.loc[0, "processed_message"] = processed_text

            rows.append(featured_df.iloc[0])

        featured_df = pd.DataFrame(rows)
        input_x = featured_df[self.feature_columns]

        return self.model.predict_proba(input_x)

    def explain_with_lime(self, message: str, num_features: int = 6):
        """
        สร้างคำอธิบายด้วย LIME จากข้อความที่ผ่าน text_process แล้ว
        """
        try:
            processed_message = text_process(message)

            # ถ้าตัดคำแล้วว่าง ให้คืนค่าว่างเลย
            if not processed_message.strip():
                return []

            explanation = self.explainer.explain_instance(
    processed_message,
    self._lime_predict_proba_processed,
    num_features=4,
    num_samples=80
)

            pred_result = self.predict(message)
            predicted_class = pred_result["prediction"]
            class_index = list(self.encoder.classes_).index(predicted_class)

            lime_items = explanation.as_list(label=class_index)

            formatted_items = []
            for word, weight in lime_items:
                formatted_items.append({
                    "feature": word,
                    "weight": round(float(weight), 4)
                })

            return formatted_items

        except Exception as e:
            print("LIME ERROR:", e)
            return []


predictor = SpamPredictor()