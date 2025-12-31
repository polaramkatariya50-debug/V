import requests
from bs4 import BeautifulSoup
import re
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# ===============================
# CONFIG
# ===============================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://vahanx.in/",
    "Accept-Language": "en-US,en;q=0.9"
}

# ===============================
# SCRAPER FUNCTION (FULL)
# ===============================
def get_comprehensive_vehicle_details(rc_number: str) -> dict:
    rc = rc_number.strip().upper()
    url = f"https://vahanx.in/rc-search/{rc}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}

    # ---------- helpers ----------
    def extract_card(label):
        for div in soup.select(".hrcd-cardbody"):
            span = div.find("span")
            if span and label.lower() in span.text.lower():
                p = div.find("p")
                return p.get_text(strip=True) if p else None
        return None

    def extract_section(title, keys):
        data = {}
        h3 = soup.find("h3", string=lambda s: s and title.lower() in s.lower())
        card = h3.find_parent("div", class_="hrc-details-card") if h3 else None
        if not card:
            return data

        for k in keys:
            sp = card.find("span", string=lambda s: s and k.lower() in s.lower())
            if sp:
                p = sp.find_next("p")
                data[k.lower().replace(" ", "_")] = p.get_text(strip=True) if p else None
        return data

    def clean(d):
        return {k: v for k, v in d.items() if v not in [None, ""]}

    # ---------- extraction ----------
    ownership = extract_section("Ownership Details", [
        "Owner Name", "Father's Name", "Owner Serial No", "Registered RTO"
    ])

    vehicle = extract_section("Vehicle Details", [
        "Model Name", "Maker Model", "Vehicle Class",
        "Fuel Type", "Fuel Norms",
        "Cubic Capacity", "Seating Capacity"
    ])

    insurance = extract_section("Insurance Information", [
        "Insurance Company", "Insurance No",
        "Insurance Expiry", "Insurance Upto"
    ])

    validity = extract_section("Important Dates", [
        "Registration Date", "Vehicle Age",
        "Fitness Upto", "Tax Upto"
    ])

    puc = extract_section("PUC Details", [
        "PUC No", "PUC Upto"
    ])

    other = extract_section("Other Information", [
        "Financer Name", "Permit Type",
        "Blacklist Status", "NOC Details"
    ])

    # ---------- final response ----------
    return {
        "status": "success",
        "registration_number": rc,
        "ownership_details": clean(ownership),
        "vehicle_details": clean(vehicle),
        "insurance": clean(insurance),
        "validity": clean(validity),
        "puc_details": clean(puc),
        "other_info": clean(other),
        "timestamp": int(time.time())
    }

# ===============================
# ROUTES (VERY IMPORTANT)
# ===============================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "VNI0X Vehicle Information API",
        "endpoint": "/api/vehicle-info?rc=DL01AB1234"
    })

@app.route("/api/vehicle-info", methods=["GET"])
def vehicle_info():
    rc = request.args.get("rc")
    if not rc:
        return jsonify({
            "error": "Missing rc parameter",
            "usage": "/api/vehicle-info?rc=DL01AB1234"
        }), 400

    data = get_comprehensive_vehicle_details(rc)
    if "error" in data:
        return jsonify(data), 500

    return jsonify(data)
