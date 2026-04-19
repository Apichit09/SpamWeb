import os
from flask import Flask, render_template, request, redirect, url_for, flash

from utils.predictor import predictor
from utils.history import save_history, load_history

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "spam-detection-secret-key")


def build_explanation(prediction: str, message: str) -> str:
    message_lower = message.lower()
    reasons = []

    if "http" in message_lower or "www." in message_lower or ".com" in message_lower:
        reasons.append("มีลิงก์หรือ URL อยู่ในข้อความ")

    if "ฟรี" in message or "รางวัล" in message or "โบนัส" in message:
        reasons.append("พบคำที่ใช้ดึงดูดความสนใจ เช่น ฟรี รางวัล หรือโบนัส")

    if "ด่วน" in message or "ภายใน" in message or "ทันที" in message:
        reasons.append("พบลักษณะข้อความเร่งด่วนหรือกดดันให้รีบดำเนินการ")

    if "ยืนยัน" in message or "บัญชี" in message or "ระงับ" in message:
        reasons.append("พบข้อความแนวแจ้งเตือนให้ยืนยันบัญชีหรือข้อมูลสำคัญ")

    if prediction == "Spam":
        if reasons:
            return "ระบบตรวจพบว่า " + " และ ".join(reasons)
        return "ข้อความนี้มีรูปแบบใกล้เคียงกับข้อความสแปมหรือข้อความชักชวนที่มีความเสี่ยง"

    return "ข้อความนี้มีลักษณะเป็นข้อความทั่วไป และไม่พบรูปแบบที่เข้าข่ายสแปมเด่นชัด"


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    message = request.form.get("message", "").strip()

    # ตรวจสอบข้อมูลนำเข้า
    if not message:
        flash("กรุณากรอกข้อความก่อนทำการตรวจสอบ", "error")
        return redirect(url_for("index"))

    if len(message) > 2000:
        flash("ข้อความยาวเกินไป กรุณาลดความยาวข้อความ", "error")
        return redirect(url_for("index"))

    # ทำนายผล
    try:
        result = predictor.predict(message)
    except Exception as e:
        print("PREDICT ERROR:", e)
        flash("เกิดข้อผิดพลาดระหว่างการวิเคราะห์ข้อความ", "error")
        return redirect(url_for("index"))

    # คำอธิบายแบบ rule-based
    rule_explanation = build_explanation(result["prediction"], message)

    # คำอธิบายแบบ LIME
    try:
        lime_explanation = predictor.explain_with_lime(message)
    except Exception as e:
        print("LIME ERROR:", e)
        lime_explanation = []

    # บันทึกประวัติ
    try:
        save_history(
            message_text=result["message"],
            predicted_label=result["prediction"],
            confidence_score=result["confidence"]
        )
    except Exception as e:
        print("SAVE HISTORY ERROR:", e)

    # แสดงผลลัพธ์
    return render_template(
        "result.html",
        message=result["message"],
        prediction=result["prediction"],
        confidence=result["confidence"],
        explanation=rule_explanation,
        lime_explanation=lime_explanation,
        recent_history=load_history()[:3]
    )


@app.route("/history", methods=["GET"])
def history():
    q = request.args.get("q", "").strip().lower()
    label_filter = request.args.get("label", "").strip()

    history_rows = load_history()

    if q:
        history_rows = [
            row for row in history_rows
            if q in row["message_text"].lower()
        ]

    if label_filter in ["Spam", "Not Spam"]:
        history_rows = [
            row for row in history_rows
            if row["predicted_label"] == label_filter
        ]

    spam_count = sum(1 for row in history_rows if row["predicted_label"] == "Spam")
    not_spam_count = sum(1 for row in history_rows if row["predicted_label"] == "Not Spam")

    return render_template(
        "history.html",
        history_rows=history_rows,
        q=q,
        label_filter=label_filter,
        total_count=len(history_rows),
        spam_count=spam_count,
        not_spam_count=not_spam_count
    )


if __name__ == "__main__":
    app.run(debug=True)