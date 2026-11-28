# Company Health Tracker

Company Health Tracker helps a supplier decide whether to offer a UK restaurant or café credit terms. The page shows a sample of companies from a PostgreSQL database. You enter a company number and click **Run model**. The backend runs our v1 decision tree on that company’s latest public-record snapshot, predicts whether it will stay active or fail (insolvency, compulsory strike-off, voluntary strike-off), and turns that prediction into a decision: **offer 60-day payment terms** or **ask for payment upfront**.

The model is trained in a separate repository: https://github.com/edwardh0408-ops/PIPAIF26_Team1_Model_v1. This app contains only the fitted tree, exported as plain if/else rules in `tree_rules.py`, plus the decision rule in `app.py`. There is no fitting or evaluation code here.

## Architecture

The app has three layers:

- **Browser.** The page in `templates/index.html` loads company rows from the API and sends a company number to the model endpoint when you click **Run model**.
- **Flask backend.** `app.py` serves the HTML page and JSON APIs. It reads `DATABASE_URL` from the environment (via a private `.env` file locally) and talks to Postgres with `psycopg2`. `tree_rules.py` is the fitted v1 decision tree as generated Python code.
- **PostgreSQL on Railway.** Company profiles and snapshot metrics live in a PostgreSQL database hosted on Railway. The app does not store data locally.

## Local setup

1. Clone the repository and open a terminal in the project root.

2. Create and activate a Python virtual environment.

   **Linux / macOS:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   **Windows (PowerShell):**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a private `.env` file in the project root. Do not commit it. It must define:

   - `DATABASE_URL` — connection string for the Railway PostgreSQL database

   Never put real connection strings, passwords, or other secrets in this README or in files that are committed to git.

5. Run the app.

   **Linux / deployment (Gunicorn):**

   ```bash
   gunicorn --bind 0.0.0.0:8000 app:app
   ```

   **Windows (Flask development server):**

   ```powershell
   python -m flask --app app run --port 8000
   ```

6. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

The Docker image uses Gunicorn the same way as Linux/deployment (`gunicorn --bind 0.0.0.0:$PORT app:app`).

## Routes

### `GET /`

Serves the Company Health Tracker page. The page fetches `/api/items` on load and posts to `/api/predict` when you enter a company number and click **Run model**.

### `GET /api/items`

Returns JSON for the first three rows of the `company` table, ordered by name. Each object has `company_number`, `company_name`, `incorporated` (`YYYY-MM-DD`), and `status_today`.

### `POST /api/predict`

Accepts JSON with a company number, for example `{"company_number": "11837902"}`.

- Loads the company’s latest row from `company_snapshot`, plus `jurisdiction` and `last_accounts_type` from `company` and SIC codes from `company_sic`.
- Runs `predict_outcome` from `tree_rules.py` and applies the decision rule:
  - predicted `active` → **Offer 60-day payment terms**
  - predicted `insolvency`, `compulsory_strike_off` or `voluntary_strike_off` → **Ask for payment upfront**
- Returns `company_number`, `company_name`, `as_of_date`, `prediction`, `prediction_label`, and `decision`.
- Missing `company_number` → HTTP 400. Company not found, or no snapshot rows → HTTP 404.

## Updating the model

Do not edit `tree_rules.py` by hand. In the model repo, run `python export_tree_rules.py`, then copy `outputs/tree_rules.py` into this repo.
