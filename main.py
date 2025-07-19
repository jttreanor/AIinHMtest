
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import json
import os

app = FastAPI()

# Load the USPSTF recommendations from the JSON file
with open("uspstf_enriched.json", "r", encoding="utf-8") as f:
    RECOMMENDATIONS = json.load(f)

# Define input model for patient data
class PatientProfile(BaseModel):
    age: int
    weight: float
    height_ft: int
    height_in: int
    sex: str
    pregnant: str
    tobacco_user: str
    sexually_active: str

def calculate_bmi_category(weight, height_ft, height_in):
    height_total_inches = height_ft * 12 + height_in
    bmi = 703 * weight / (height_total_inches ** 2)
    if bmi < 18.5:
        return "UW"
    elif bmi < 25:
        return "N"
    elif bmi < 30:
        return "O"
    else:
        return "OB"

@app.post("/get_recommendations")
def get_recommendations(profile: PatientProfile) -> Dict[str, List[Dict]]:
    bmi_category = calculate_bmi_category(profile.weight, profile.height_ft, profile.height_in)

    results_by_grade = {"A": [], "B": [], "C": [], "D": [], "I": []}

    for rec in RECOMMENDATIONS:
        if not (rec["age_min"] <= profile.age <= rec["age_max"]):
            continue
        if rec["sex"] != "all" and rec["sex"] != profile.sex:
            continue
        if rec["bmi_tag"] != "ALL" and rec["bmi_tag"] != bmi_category:
            continue
        risk = rec.get("raw_risk_name", "").lower()
        if risk:
            if "pregnant" in risk and profile.pregnant != "yes":
                continue
            if "tobacco" in risk and profile.tobacco_user != "yes":
                continue
            if "sexually active" in risk and profile.sexually_active != "yes":
                continue
        result = {
            "id": rec["id"],
            "title": rec["title"],
            "recommendation": rec["recommendation"],
            "frequency": rec["frequency_of_service"]
        }
        results_by_grade.get(rec["grade"], []).append(result)

    return results_by_grade
