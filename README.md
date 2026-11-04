# Company Health Tracker

Company Health Tracker is a web app that lists UK company records from a PostgreSQL database and lets you compare a company’s age (in years) against the average age stored in snapshot data. The browser shows a table of company names, incorporation dates, and current status, plus a simple form that posts a numeric age to a model endpoint and reports whether that age is above or below the average.

## Architecture

The app has three layers:

- **Browser.** The page in `templates/index.html` loads company rows from the API and sends an age value when you run the model.
- **Flask backend.** `app.py` serves the HTML page and JSON APIs. It reads `DATABASE_URL` from the environment (via a private `.env` file locally) and talks to Postgres with `psycopg2`.
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

Serves the Company Health Tracker page. The page fetches `/api/items` on load and posts to `/api/predict` when you enter a company age and click **Run model**.

### `GET /api/items`

Returns JSON for every row in the `company` table, ordered by name. Each object has:

- `company_name`
- `incorporated` (from `date_of_creation`, formatted as `YYYY-MM-DD`)
- `status_today` (from `company_status`)

The table on the home page uses this list. Status values such as active, liquidation, and dissolved are colored in the UI.

### `POST /api/predict`

Accepts JSON with a numeric `value` (company age in years), for example `{"value": 12}`.

- If `value` is missing or not a finite number, the API responds with HTTP 400 and `{"error": "..."}`.
- On success it calls `run_model` in `model.py` and returns JSON with `input`, `average_age`, `difference`, and `label` (`above average` or `below average`).

The current implementation compares the submitted age to `AVG(age_years)` from `company_snapshot`.

## Model placeholder

`model.py` contains **placeholder logic**. It only compares the submitted age to the average `age_years` in `company_snapshot`. Replace this with the team’s real analysis when that work is ready.
