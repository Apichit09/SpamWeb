import re
import pandas as pd
from pythainlp.tokenize import word_tokenize


def text_process(text: str) -> str:
    text = str(text).strip().lower()

    text = re.sub(r'https?://\S+|www\.\S+|\S+\.(com|net|org|co|me|ly|io|ai)\S*', ' ', text)
    text = re.sub(r'\b\d{2,3}-\d{3,4}-\d{4}\b', ' ', text)
    text = re.sub(r'\b\d{9,10}\b', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9ก-๙\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = word_tokenize(text, engine="newmm")
    tokens = [tok.strip() for tok in tokens if tok.strip()]

    return " ".join(tokens)


def create_features(df_input: pd.DataFrame) -> pd.DataFrame:
    df_out = df_input.copy()
    df_out["message"] = df_out["message"].fillna("").astype(str)

    df_out["message_length"] = df_out["message"].str.len()
    df_out["digit_count"] = df_out["message"].str.count(r"\d")
    df_out["uppercase_ratio"] = df_out["message"].str.count(r"[A-Z]") / (df_out["message_length"] + 1e-6)
    df_out["repeated_punctuation_count"] = df_out["message"].str.count(r"([!?.])\1{1,}")
    df_out["url_count"] = df_out["message"].str.count(r"https?://\S+|www\.\S+|\S+\.\S+")

    short_url_pattern = r"bit\.ly|cutt\.ly|t\.co|rebrand\.ly|shorturl\.asia|line\.me|lin\.ee"
    df_out["has_short_url"] = df_out["message"].str.contains(short_url_pattern, case=False, regex=True).astype(int)

    phone_pattern = r"(\d{2,3}-\d{3,4}-\d{4}|\d{9,10})"
    df_out["has_phone"] = df_out["message"].str.contains(phone_pattern, regex=True).astype(int)

    df_out["has_line_keyword"] = df_out["message"].str.contains(r"line|ไลน์|แอดไลน์", case=False, regex=True).astype(int)

    advertisement_keywords = [
        "โปรโมชั่น", "ส่วนลด", "ช้อป", "สาขา", "คลิกเลย", "แบรนด์",
        "คอลเลคชั่น", "โค้ด", "flash sale", "ลดราคา", "sale", "ฟรี"
    ]
    df_out["advertisement_words_count"] = df_out["message"].str.count("|".join(advertisement_keywords)).astype(int)

    brand_keywords = ["Lazada", "Shopee", "AIS", "dtac", "True", "KFC", "Grab", "Central", "Uniqlo", "SCB", "KBank"]
    df_out["is_known_brand"] = df_out["message"].str.contains("|".join(brand_keywords), case=False, regex=True).astype(int)

    df_out["is_gambling_keyword"] = df_out["message"].str.contains(
        r"เว็บตรง|pg|joker|สล็อต|บาคาร่า|คาสิโน|แทงหวย|ฝากถอน|ยูสใหม่|แตกง่าย",
        case=False,
        regex=True
    ).astype(int)

    df_out["is_loan_keyword"] = df_out["message"].str.contains(
        r"สินเชื่อ|เงินด่วน|อนุมัติไว|วงเงินกู้|กู้ได้|ไม่เช็คบูโร",
        case=False,
        regex=True
    ).astype(int)

    df_out["is_job_offer_keyword"] = df_out["message"].str.contains(
        r"ทำงานที่บ้าน|รายได้ต่อวัน|part-time|พาร์ทไทม์|รับสมัคร",
        case=False,
        regex=True
    ).astype(int)

    emotional_words = [
        "ฟรี", "รางวัล", "แจก", "โบนัส", "เครดิต", "รับสิทธิ์", "เงินคืน",
        "ด่วน", "ภายใน", "จำกัด", "เท่านั้น", "ผิดปกติ", "ถูกระงับ", "มีปัญหา"
    ]
    df_out["emotional_words_count"] = df_out["message"].str.count("|".join(emotional_words)).astype(int)

    obfuscated_pattern = r"\b[ก-ฮ]*[a-zA-Z0-9]+[ก-ฮ]+[a-zA-Z0-9]*\b"
    df_out["obfuscated_word_count"] = df_out["message"].str.count(obfuscated_pattern)

    df_out["processed_message"] = df_out["message"].apply(text_process)
    df_out["word_diversity_ratio"] = df_out["processed_message"].apply(
        lambda x: len(set(x.split())) / (len(x.split()) + 1e-6)
    )

    return df_out