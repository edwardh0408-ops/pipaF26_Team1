"""Create the company schema in Postgres and load sample_raw.json plus sample_companies.csv.

Repeating values are stored in the bridge and child tables: SIC codes, previous
names, persons entitled to a charge, resolution subcategories, filing attributes,
and share-capital lines. This extract has no semicolon-joined tools or
availability columns.
"""

import csv
import json
from decimal import Decimal
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
SCHEMA_PATH = ROOT / "schema.sql"
JSON_PATH = ROOT / "sample_raw.json"
CSV_PATH = ROOT / "sample_companies.csv"

TABLES = [
    "company_snapshot",
    "charge_transaction",
    "charge_person_entitled",
    "charge",
    "share_capital",
    "associated_filing_attribute",
    "associated_filing",
    "resolution_subcategory",
    "filing_resolution",
    "filing_attribute",
    "filing",
    "officer_appointment",
    "person",
    "previous_company_name",
    "company_sic",
    "company",
]


def database_url():
    if not ENV_PATH.exists():
        raise SystemExit(f"Missing {ENV_PATH.name}")
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "DATABASE_URL":
            url = value.strip().strip('"').strip("'")
            if "sslmode=" not in url:
                url += "&" if "?" in url else "?"
                url += "sslmode=require"
            return url
    raise SystemExit("DATABASE_URL is not set in .env")


def sql_statements(sql):
    lines = []
    for line in sql.splitlines():
        comment = line.find("--")
        if comment != -1:
            line = line[:comment]
        lines.append(line)
    statements = []
    for chunk in "\n".join(lines).split(";"):
        text = chunk.strip()
        if text:
            statements.append(text)
    return statements


def last_segment(path):
    return path.rstrip("/").split("/")[-1]


def officer_id(officer):
    return officer["links"]["officer"]["appointments"].strip("/").split("/")[1]


def blank(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def as_int(value):
    text = blank(value)
    return None if text is None else int(text)


def as_decimal(value):
    text = blank(value)
    return None if text is None else Decimal(text)


def as_bool_flag(value):
    text = blank(value)
    if text is None:
        return None
    if text in {"0", "0.0", "false", "False"}:
        return False
    if text in {"1", "1.0", "true", "True"}:
        return True
    raise ValueError(f"Expected a boolean flag, got {value!r}")


def amount(figure):
    return Decimal(str(figure).replace(",", ""))


def subcategories(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def insert_rows(cur, table, columns, rows):
    if not rows:
        return
    column_sql = ", ".join(columns)
    execute_values(
        cur,
        f"INSERT INTO {table} ({column_sql}) VALUES %s",
        rows,
        page_size=500,
    )


def company_row(record):
    profile = record["profile"]
    accounts = profile["accounts"]
    last_accounts = accounts.get("last_accounts") or {}
    next_accounts = accounts.get("next_accounts") or {}
    reference = accounts["accounting_reference_date"]
    confirmation = profile.get("confirmation_statement") or {}
    address = profile.get("registered_office_address") or {}
    return (
        profile["company_number"],
        profile["company_name"],
        profile["company_status"],
        profile.get("company_status_detail"),
        profile["type"],
        profile["jurisdiction"],
        profile["date_of_creation"],
        profile.get("date_of_cessation"),
        profile["can_file"],
        profile["has_charges"],
        profile["has_insolvency_history"],
        profile["has_super_secure_pscs"],
        profile["registered_office_is_in_dispute"],
        profile["undeliverable_registered_office_address"],
        address.get("address_line_1"),
        address.get("address_line_2"),
        address.get("locality"),
        address.get("region"),
        address.get("postal_code"),
        address.get("country"),
        int(reference["day"]),
        int(reference["month"]),
        last_accounts.get("made_up_to"),
        last_accounts.get("period_start_on"),
        last_accounts.get("period_end_on"),
        last_accounts.get("type"),
        next_accounts.get("due_on"),
        next_accounts.get("period_start_on"),
        next_accounts.get("period_end_on"),
        next_accounts.get("overdue"),
        confirmation.get("last_made_up_to"),
        confirmation.get("next_due"),
        confirmation.get("next_made_up_to"),
        confirmation.get("overdue"),
    )


def appointment_row(company_number, officer):
    address = officer.get("address") or {}
    dob = officer.get("date_of_birth") or {}
    verification = officer.get("identity_verification_details") or {}
    return (
        last_segment(officer["links"]["self"]),
        company_number,
        officer_id(officer),
        officer["person_number"],
        officer["officer_role"],
        officer["appointed_on"],
        officer.get("resigned_on"),
        officer["is_pre_1992_appointment"],
        officer.get("nationality"),
        officer.get("country_of_residence"),
        dob.get("month"),
        dob.get("year"),
        address.get("premises"),
        address.get("address_line_1"),
        address.get("address_line_2"),
        address.get("locality"),
        address.get("region"),
        address.get("postal_code"),
        address.get("country"),
        verification.get("appointment_verification_statement_due_on"),
    )


def scalar_attributes(values, owner):
    rows = []
    for name, value in values.items():
        if isinstance(value, (dict, list)):
            raise ValueError(f"{owner} attribute {name} is not a single value: {value!r}")
        rows.append((name, str(value)))
    return rows


def build_rows(companies, snapshots):
    company_rows = []
    sic_rows = []
    previous_name_rows = []
    people = {}
    appointment_rows = []
    filing_rows = []
    filing_attribute_rows = []
    resolution_rows = []
    subcategory_rows = []
    associated_rows = []
    associated_attribute_rows = []
    capital_rows = []
    charge_rows = []
    entitled_rows = []
    charge_tx_rows = []
    snapshot_rows = []

    resolution_id = 0
    associated_id = 0
    charge_tx_id = 0

    for record in companies:
        profile = record["profile"]
        company_number = profile["company_number"]
        company_rows.append(company_row(record))

        for position, code in enumerate(profile.get("sic_codes") or [], start=1):
            sic_rows.append((company_number, position, code))

        for previous in profile.get("previous_company_names") or []:
            previous_name_rows.append(
                (
                    company_number,
                    previous["effective_from"],
                    previous["name"],
                    previous["ceased_on"],
                )
            )

        for officer in record.get("officers") or []:
            person_key = officer_id(officer)
            name = officer["name"]
            if person_key in people and people[person_key] != name:
                raise ValueError(f"{person_key} has both {people[person_key]!r} and {name!r}")
            people[person_key] = name
            appointment_rows.append(appointment_row(company_number, officer))

        for filing in record.get("filing_history") or []:
            transaction_id = filing["transaction_id"]
            filing_rows.append(
                (
                    transaction_id,
                    company_number,
                    filing.get("barcode"),
                    filing["type"],
                    filing["category"],
                    filing.get("subcategory"),
                    filing["description"],
                    filing["date"],
                    filing.get("action_date"),
                    filing["pages"],
                    bool(filing.get("paper_filed", False)),
                )
            )
            for name, value in scalar_attributes(
                filing.get("description_values") or {}, transaction_id
            ):
                filing_attribute_rows.append((transaction_id, name, value))

            for resolution in filing.get("resolutions") or []:
                resolution_id += 1
                details = resolution.get("description_values") or {}
                extra = set(details) - {"case_start_date", "resolution_date"}
                if extra:
                    raise ValueError(f"Unexpected resolution values on {transaction_id}: {sorted(extra)}")
                resolution_rows.append(
                    (
                        resolution_id,
                        transaction_id,
                        resolution["category"],
                        resolution["type"],
                        resolution["description"],
                        resolution.get("original_description"),
                        details.get("case_start_date"),
                        details.get("resolution_date"),
                    )
                )
                for subcategory in subcategories(resolution.get("subcategory")):
                    subcategory_rows.append((resolution_id, subcategory))

            for associated in filing.get("associated_filings") or []:
                associated_id += 1
                associated_rows.append(
                    (
                        associated_id,
                        transaction_id,
                        associated["type"],
                        associated["category"],
                        associated["description"],
                        associated["date"],
                        associated.get("action_date"),
                    )
                )
                for name, value in (associated.get("description_values") or {}).items():
                    if name == "capital":
                        for line in value:
                            capital_rows.append(
                                (associated_id, line["currency"], amount(line["figure"]))
                            )
                        continue
                    if isinstance(value, (dict, list)):
                        raise ValueError(
                            f"Unexpected associated value {name} on {transaction_id}: {value!r}"
                        )
                    associated_attribute_rows.append((associated_id, name, str(value)))

        for charge in record.get("charges") or []:
            particulars = charge["particulars"]
            classification = charge["classification"]
            charge_rows.append(
                (
                    company_number,
                    charge["charge_number"],
                    charge["charge_code"],
                    charge["status"],
                    classification["type"],
                    classification["description"],
                    charge["created_on"],
                    charge["delivered_on"],
                    particulars["contains_fixed_charge"],
                    particulars["contains_floating_charge"],
                    particulars["contains_negative_pledge"],
                    particulars["floating_charge_covers_all"],
                    particulars["description"],
                )
            )
            for person in charge.get("persons_entitled") or []:
                entitled_rows.append(
                    (company_number, charge["charge_number"], person["name"])
                )
            for transaction in charge.get("transactions") or []:
                charge_tx_id += 1
                filing_link = (transaction.get("links") or {}).get("filing")
                charge_tx_rows.append(
                    (
                        charge_tx_id,
                        company_number,
                        charge["charge_number"],
                        transaction["delivered_on"],
                        transaction["filing_type"],
                        last_segment(filing_link) if filing_link else None,
                    )
                )

    for row in snapshots:
        company_number = row["company_number"]
        snapshot_rows.append(
            (
                company_number,
                row["as_of_date"],
                as_decimal(row["age_years"]),
                as_int(row["accounts_filings"]),
                as_decimal(row["avg_days_late_accounts"]),
                as_decimal(row["max_days_late_accounts"]),
                as_decimal(row["days_since_last_accounts"]),
                as_int(row["directors_active"]),
                as_int(row["director_resignations_12m"]),
                as_int(row["director_appointments_12m"]),
                as_int(row["address_changes"]),
                as_int(row["strike_off_warnings"]),
                as_int(row["charges_created"]),
                as_int(row["charges_outstanding"]),
                as_int(row["filings_total"]),
                row["outcome"],
                row["outcome_date"],
                as_bool_flag(row["failed_within_12m"]),
            )
        )

    return {
        "company": company_rows,
        "company_sic": sic_rows,
        "previous_company_name": previous_name_rows,
        "person": [(key, name) for key, name in people.items()],
        "officer_appointment": appointment_rows,
        "filing": filing_rows,
        "filing_attribute": filing_attribute_rows,
        "filing_resolution": resolution_rows,
        "resolution_subcategory": subcategory_rows,
        "associated_filing": associated_rows,
        "associated_filing_attribute": associated_attribute_rows,
        "share_capital": capital_rows,
        "charge": charge_rows,
        "charge_person_entitled": entitled_rows,
        "charge_transaction": charge_tx_rows,
        "company_snapshot": snapshot_rows,
    }


def main():
    companies = json.loads(JSON_PATH.read_text())
    with CSV_PATH.open(newline="") as handle:
        snapshots = list(csv.DictReader(handle))
    rows = build_rows(companies, snapshots)

    connection = psycopg2.connect(database_url())
    try:
        with connection:
            with connection.cursor() as cur:
                for table in TABLES:
                    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                for statement in sql_statements(SCHEMA_PATH.read_text()):
                    cur.execute(statement)

                insert_rows(
                    cur,
                    "company",
                    [
                        "company_number",
                        "company_name",
                        "company_status",
                        "company_status_detail",
                        "company_type",
                        "jurisdiction",
                        "date_of_creation",
                        "date_of_cessation",
                        "can_file",
                        "has_charges",
                        "has_insolvency_history",
                        "has_super_secure_pscs",
                        "registered_office_is_in_dispute",
                        "undeliverable_registered_office_address",
                        "address_line_1",
                        "address_line_2",
                        "locality",
                        "region",
                        "postal_code",
                        "country",
                        "accounting_ref_day",
                        "accounting_ref_month",
                        "last_accounts_made_up_to",
                        "last_accounts_period_start",
                        "last_accounts_period_end",
                        "last_accounts_type",
                        "next_accounts_due_on",
                        "next_accounts_period_start",
                        "next_accounts_period_end",
                        "next_accounts_overdue",
                        "confirmation_last_made_up_to",
                        "confirmation_next_due",
                        "confirmation_next_made_up_to",
                        "confirmation_overdue",
                    ],
                    rows["company"],
                )
                insert_rows(cur, "company_sic", ["company_number", "position", "sic_code"], rows["company_sic"])
                insert_rows(
                    cur,
                    "previous_company_name",
                    ["company_number", "effective_from", "name", "ceased_on"],
                    rows["previous_company_name"],
                )
                insert_rows(cur, "person", ["officer_id", "name"], rows["person"])
                insert_rows(
                    cur,
                    "officer_appointment",
                    [
                        "appointment_id",
                        "company_number",
                        "officer_id",
                        "person_number",
                        "officer_role",
                        "appointed_on",
                        "resigned_on",
                        "is_pre_1992_appointment",
                        "nationality",
                        "country_of_residence",
                        "dob_month",
                        "dob_year",
                        "premises",
                        "address_line_1",
                        "address_line_2",
                        "locality",
                        "region",
                        "postal_code",
                        "country",
                        "appointment_verification_due_on",
                    ],
                    rows["officer_appointment"],
                )
                insert_rows(
                    cur,
                    "filing",
                    [
                        "transaction_id",
                        "company_number",
                        "barcode",
                        "filing_type",
                        "category",
                        "subcategory",
                        "description",
                        "filed_on",
                        "action_date",
                        "pages",
                        "paper_filed",
                    ],
                    rows["filing"],
                )
                insert_rows(
                    cur,
                    "filing_attribute",
                    ["transaction_id", "attribute_name", "attribute_value"],
                    rows["filing_attribute"],
                )
                insert_rows(
                    cur,
                    "filing_resolution",
                    [
                        "resolution_id",
                        "transaction_id",
                        "category",
                        "resolution_type",
                        "description",
                        "original_description",
                        "case_start_date",
                        "resolution_date",
                    ],
                    rows["filing_resolution"],
                )
                insert_rows(
                    cur,
                    "resolution_subcategory",
                    ["resolution_id", "subcategory"],
                    rows["resolution_subcategory"],
                )
                insert_rows(
                    cur,
                    "associated_filing",
                    [
                        "associated_filing_id",
                        "transaction_id",
                        "filing_type",
                        "category",
                        "description",
                        "filed_on",
                        "action_date",
                    ],
                    rows["associated_filing"],
                )
                insert_rows(
                    cur,
                    "associated_filing_attribute",
                    ["associated_filing_id", "attribute_name", "attribute_value"],
                    rows["associated_filing_attribute"],
                )
                insert_rows(
                    cur,
                    "share_capital",
                    ["associated_filing_id", "currency", "amount"],
                    rows["share_capital"],
                )
                insert_rows(
                    cur,
                    "charge",
                    [
                        "company_number",
                        "charge_number",
                        "charge_code",
                        "status",
                        "classification_type",
                        "classification_description",
                        "created_on",
                        "delivered_on",
                        "contains_fixed_charge",
                        "contains_floating_charge",
                        "contains_negative_pledge",
                        "floating_charge_covers_all",
                        "particulars_description",
                    ],
                    rows["charge"],
                )
                insert_rows(
                    cur,
                    "charge_person_entitled",
                    ["company_number", "charge_number", "name"],
                    rows["charge_person_entitled"],
                )
                insert_rows(
                    cur,
                    "charge_transaction",
                    [
                        "charge_transaction_id",
                        "company_number",
                        "charge_number",
                        "delivered_on",
                        "filing_type",
                        "filing_transaction_id",
                    ],
                    rows["charge_transaction"],
                )
                insert_rows(
                    cur,
                    "company_snapshot",
                    [
                        "company_number",
                        "as_of_date",
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
                        "outcome",
                        "outcome_date",
                        "failed_within_12m",
                    ],
                    rows["company_snapshot"],
                )

                print("table\trows")
                for table in reversed(TABLES):
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    print(f"{table}\t{cur.fetchone()[0]}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
