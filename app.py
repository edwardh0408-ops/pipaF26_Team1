import os
from datetime import date, datetime

import psycopg2
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from psycopg2.extras import RealDictCursor

load_dotenv()

app = Flask(__name__)

ITEMS_QUERY = """
SELECT company_name, date_of_creation AS incorporated, company_status AS status_today
FROM company
ORDER BY company_name
"""


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
            "company_name": row["company_name"],
            "incorporated": format_incorporated(row["incorporated"]),
            "status_today": row["status_today"],
        }
        for row in rows
    ]
    return jsonify(items)


if __name__ == "__main__":
    app.run(debug=True)
