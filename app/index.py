import requests
from bs4 import BeautifulSoup
import re
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://vahanx.in/",
    "Accept-Language": "en-US,en;q=0.9",
}

# ================================
# CORE SCRAPER
# ================================
def get_comprehensive_vehicle_details(rc_number: str) -> dict:
    rc = rc_number.strip().upper()
    url = f"https://vahanx.in/rc-search/{rc}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        return {"error": f"Request failed: {e}"}

    def card_value(label):
        for div in soup.select(".hrcd-cardbody"):
            s = div.find("span")
            if s and label.lower() in s.text.lower():
                p = div.find("p")
                return p.text.strip() if p else None
        return None

    def section(header, keys):
        result = {}
        h = soup.find("h3", string=lambda s: s and header.lower() in s.lower())
        box = h.find_parent("div", class_="hrc-details-card") if h else None
        if not box:
            return result

        for k in keys:
            sp = box.find("span", string=lambda s: s and k.lower() in s.lower())
            if sp:
                val = sp.find_next("p")
                result[k.lower().replace(" ", "_")] = val.text.strip() if val else None
        return result

    def clean(d):
        return {k: v for k, v in d.items() if v not in [None, ""]}

    # MAIN EXTRACTION
    ownership = section("Ownership Details", [
        "Owner Name", "Father's Name", "Owner Serial No", "Registered RTO"
    ])

    vehicle = section("Vehicle Details", [
        "Model Name", "Maker Model", "Vehicle Class",
        "Fuel Type", "Fuel Norms",
        "Cubic Capacity", "Seating Capacity"
    ])

    insurance = section("Insurance Information", [
        "Insurance Company", "Insurance No",
        "Insurance Expiry", "Insurance Upto"
    ])

    validity = section("Important Dates", [
        "Registration Date", "Vehicle Age",
        "Fitness Upto", "Tax Upto"
    ])

    puc = section("PUC Details", ["PUC No", "PUC Upto"])

    other = section("Other Information", [
        "Financer Name", "Permit Type",
        "Blacklist Status", "NOC Details"
    ])

    return clean({
        "status": "success",
        "registration_number": rc,
        "ownership": clean(ownership),
        "vehicle": clean(vehicle),
        "insurance": clean(insurance),
        "validity": clean(validity),
        "puc": clean(puc),
        "other": clean(other),
        "timestamp": int(time.time())
    })

# ================================
# ROUTES
# ================================
@app.route("/")
def home():
    return jsonify({
        "service": "VNI0X Vehicle Information API",
        "usage": "/api/vehicle-info?rc=DL01AB1234"
    })

@app.route("/api/vehicle-info")
def vehicle_info():
    rc = request.args.get("rc")
    if not rc:
        return jsonify({"error": "rc parameter missing"}), 400

    data = get_comprehensive_vehicle_details(rc)
    if "error" in data:
        return jsonify(data), 500

    return jsonify(data)
