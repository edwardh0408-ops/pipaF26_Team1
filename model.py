import os

import psycopg2

AVERAGE_AGE_QUERY = "SELECT AVG(age_years) FROM company_snapshot"


def get_database_url():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return database_url


def run_model(value):
    with psycopg2.connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(AVERAGE_AGE_QUERY)
            average = cur.fetchone()[0]

    if average is None:
        raise RuntimeError("company_snapshot has no age_years values")

    average_age = round(float(average), 2)
    difference = round(float(value) - float(average), 2)
    label = "above average" if difference > 0 else "below average"
    return {
        "input": value,
        "average_age": average_age,
        "difference": difference,
        "label": label,
    }
