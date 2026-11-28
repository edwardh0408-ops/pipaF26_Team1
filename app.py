import os
from datetime import date, datetime

import psycopg2
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from psycopg2.extras import RealDictCursor

from tree_rules import predict_outcome

load_dotenv()

app = Flask(__name__)

ITEMS_QUERY = """
SELECT company_number, company_name, date_of_creation AS incorporated, company_status AS status_today
FROM company
ORDER BY company_name
LIMIT 3
"""

# One row of model inputs for a company: its latest yearly snapshot, plus the
# profile fields the tree also uses (jurisdiction, last accounts type, SIC codes).
FEATURES_QUERY = """
SELECT
    c.company_number,
    c.company_name,
    c.jurisdiction,
    c.last_accounts_type,
    s.as_of_date,
    s.age_years,
    s.accounts_filings,
    s.avg_days_late_accounts,
    s.max_days_late_accounts,
    s.days_since_last_accounts,
    s.directors_active,
    s.director_resignations_12m,
    s.director_appointments_12m,
    s.address_changes,
    s.strike_off_warnings,
    s.charges_created,
    s.charges_outstanding,
    s.filings_total,
    (SELECT COUNT(*) FROM company_sic cs WHERE cs.company_number = c.company_number) AS n_sic_codes,
    (SELECT sic_code FROM company_sic cs WHERE cs.company_number = c.company_number AND position = 1) AS sic_1,
    (SELECT sic_code FROM company_sic cs WHERE cs.company_number = c.company_number AND position = 2) AS sic_2,
    (SELECT sic_code FROM company_sic cs WHERE cs.company_number = c.company_number AND position = 3) AS sic_3,
    (SELECT sic_code FROM company_sic cs WHERE cs.company_number = c.company_number AND position = 4) AS sic_4
FROM company c
JOIN company_snapshot s ON s.company_number = c.company_number
WHERE c.company_number = %s
ORDER BY s.as_of_date DESC
LIMIT 1
"""

NUMERIC_FEATURES = [
    "age_years",
    "accounts_filings",
    "avg_days_late_accounts",
    "max_days_late_accounts",
    "days_since_last_accounts",
    "directors_active",
    "director_resignations_12m",
    "director_appointments_12m",
    "address_changes",
    "strike_off_warnings",
    "charges_created",
    "charges_outstanding",
    "filings_total",
    "n_sic_codes",
]

OUTCOME_LABELS = {
    "active": "stays active",
    "insolvency": "insolvency",
    "compulsory_strike_off": "compulsory strike-off",
    "voluntary_strike_off": "voluntary strike-off",
}


def get_database_url():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return database_url


def format_incorporated(value):
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    if value is None:
        return None
    return str(value)


def model_inputs(row):
    """Turn a FEATURES_QUERY row into the dict the tree expects."""
    features = {}
    for name in NUMERIC_FEATURES:
        value = row[name]
        features[name] = None if value is None else float(value)
    for name in ["sic_1", "sic_2", "sic_3", "sic_4"]:
        features[name] = (row[name] or "none").strip()
    features["jurisdiction"] = row["jurisdiction"]
    features["last_accounts_type"] = row["last_accounts_type"] or "no_accounts"
    return features


def credit_decision(outcome):
    """Decision rule: turn the predicted outcome into a credit action."""
    if outcome == "active":
        return "Offer 60-day payment terms"
    return "Ask for payment upfront"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/items")
def api_items():
    with psycopg2.connect(get_database_url()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(ITEMS_QUERY)
            rows = cur.fetchall()

    items = [
        {
            "company_number": row["company_number"],
            "company_name": row["company_name"],
            "incorporated": format_incorporated(row["incorporated"]),
            "status_today": row["status_today"],
        }
        for row in rows
    ]
    return jsonify(items)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    body = request.get_json(silent=True)
    company_number = body.get("company_number") if isinstance(body, dict) else None
    if not isinstance(company_number, str) or not company_number.strip():
        return jsonify({"error": "company_number is required"}), 400
    company_number = company_number.strip().upper()

    with psycopg2.connect(get_database_url()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(FEATURES_QUERY, (company_number,))
            row = cur.fetchone()

    if row is None:
        return jsonify({"error": f"No snapshot data for company {company_number}"}), 404

    outcome = predict_outcome(model_inputs(row))
    return jsonify(
        {
            "company_number": row["company_number"],
            "company_name": row["company_name"],
            "as_of_date": format_incorporated(row["as_of_date"]),
            "prediction": outcome,
            "prediction_label": OUTCOME_LABELS.get(outcome, outcome),
            "decision": credit_decision(outcome),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
