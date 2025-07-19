
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
from collections import defaultdict
import json

app = FastAPI()

# Load recommendations from local JSON file
with open("uspstf_enriched.json", "r", encoding="utf-8") as f:
    RECOMMENDATIONS = json.load(f)

class PatientProfile(BaseModel):
    age: int
    weight: float
    height_ft: int
    height_in: int
    sex: str
    pregnant: str
    tobacco_user: str
    sexually_active: str

def calculate_bmi(weight, height_ft, height_in):
    try:
        total_height_in = height_ft * 12 + height_in
        bmi = 703 * weight / (total_height_in ** 2)
        return round(bmi, 1)
    except:
        return None

def classify_bmi(bmi):
    if bmi is None:
        return None
    if bmi < 18.5:
        return "UW"
    elif bmi < 25:
        return "N"
    elif bmi < 30:
        return "O"
    else:
        return "OB"

def matches_risk_tag(rec, pregnant, tobacco_user, sexually_active, bmi_category):
    risk_tag = rec.get("raw_risk_name", "").strip().lower()
    bmi_tag = rec.get("bmi_tag", "ALL").upper()

    if risk_tag == "pregnant" and pregnant != "yes":
        return False
    if risk_tag == "tobacco user" and tobacco_user != "yes":
        return False
    if risk_tag == "sexually active" and sexually_active != "yes":
        return False

    if bmi_tag != "ALL" and bmi_category and bmi_tag != bmi_category:
        return False

    return True

def search_recommendations(data, age, sex, pregnant, tobacco_user, sexually_active, bmi_category):
    matches = []
    for rec in data:
        if not (rec["age_min"] <= age <= rec["age_max"]):
            continue
        rec_sex = rec.get("sex", "all").lower()
        if sex and rec_sex not in [sex, "all", "men and women"]:
            continue
        if matches_risk_tag(rec, pregnant, tobacco_user, sexually_active, bmi_category):
            matches.append(rec)
    return matches

@app.post("/get_recommendations")
def get_recommendations(profile: PatientProfile) -> Dict[str, List[Dict]]:
    bmi = calculate_bmi(profile.weight, profile.height_ft, profile.height_in)
    bmi_category = classify_bmi(bmi)

    matched = search_recommendations(
        RECOMMENDATIONS,
        profile.age,
        profile.sex,
        profile.pregnant,
        profile.tobacco_user,
        profile.sexually_active,
        bmi_category
    )

    result = defaultdict(list)
    for rec in matched:
        grade = rec.get("grade", "UNSPECIFIED").upper()
        result[grade].append({
            "id": rec.get("id"),
            "title": rec.get("title"),
            "recommendation": rec.get("recommendation"),
            "frequency": rec.get("frequency_of_service"),
            "risk_factor": rec.get("risk_factor"),
            "age_range": f"{rec['age_min']}–{rec['age_max']}",
            "sex": rec.get("sex")
        })

    return result
