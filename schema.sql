-- Companies House company data, for Postgres.
-- Source tables come from sample_raw.json.
-- company_snapshot is the derived one-row-per-company table from sample_companies.csv.

CREATE TABLE company (
    company_number VARCHAR PRIMARY KEY,
    company_name VARCHAR NOT NULL,
    company_status VARCHAR NOT NULL,
    company_status_detail VARCHAR,
    company_type VARCHAR NOT NULL,
    jurisdiction VARCHAR NOT NULL,
    date_of_creation DATE NOT NULL,
    date_of_cessation DATE,
    can_file BOOLEAN NOT NULL,
    has_charges BOOLEAN NOT NULL,
    has_insolvency_history BOOLEAN NOT NULL,
    has_super_secure_pscs BOOLEAN NOT NULL,
    registered_office_is_in_dispute BOOLEAN NOT NULL,
    undeliverable_registered_office_address BOOLEAN NOT NULL,
    address_line_1 VARCHAR,
    address_line_2 VARCHAR,
    locality VARCHAR,
    region VARCHAR,
    postal_code VARCHAR,
    country VARCHAR,
    accounting_ref_day SMALLINT NOT NULL,
    accounting_ref_month SMALLINT NOT NULL,
    last_accounts_made_up_to DATE,
    last_accounts_period_start DATE,
    last_accounts_period_end DATE,
    last_accounts_type VARCHAR,
    next_accounts_due_on DATE,
    next_accounts_period_start DATE,
    next_accounts_period_end DATE,
    next_accounts_overdue BOOLEAN,
    confirmation_last_made_up_to DATE,
    confirmation_next_due DATE,
    confirmation_next_made_up_to DATE,
    confirmation_overdue BOOLEAN
);

-- position 1 is the sic_1 column in the CSV.
CREATE TABLE company_sic (
    company_number VARCHAR NOT NULL,
    position SMALLINT NOT NULL,
    sic_code CHAR(5) NOT NULL,
    PRIMARY KEY (company_number, position),
    FOREIGN KEY (company_number) REFERENCES company (company_number)
);

CREATE TABLE previous_company_name (
    company_number VARCHAR NOT NULL,
    effective_from DATE NOT NULL,
    name VARCHAR NOT NULL,
    ceased_on DATE NOT NULL,
    PRIMARY KEY (company_number, effective_from),
    FOREIGN KEY (company_number) REFERENCES company (company_number)
);

-- officer_id is the id in /officers/{id}/appointments.
CREATE TABLE person (
    officer_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL
);

-- appointment_id is the id in /company/{n}/appointments/{id}.
-- One person can have several appointments at the same company.
CREATE TABLE officer_appointment (
    appointment_id VARCHAR PRIMARY KEY,
    company_number VARCHAR NOT NULL,
    officer_id VARCHAR NOT NULL,
    person_number VARCHAR NOT NULL,
    officer_role VARCHAR NOT NULL,
    appointed_on DATE NOT NULL,
    resigned_on DATE,
    is_pre_1992_appointment BOOLEAN NOT NULL,
    nationality VARCHAR,
    country_of_residence VARCHAR,
    dob_month SMALLINT,
    dob_year SMALLINT,
    premises VARCHAR,
    address_line_1 VARCHAR,
    address_line_2 VARCHAR,
    locality VARCHAR,
    region VARCHAR,
    postal_code VARCHAR,
    country VARCHAR,
    appointment_verification_due_on DATE,
    FOREIGN KEY (company_number) REFERENCES company (company_number),
    FOREIGN KEY (officer_id) REFERENCES person (officer_id)
);

CREATE TABLE filing (
    transaction_id VARCHAR PRIMARY KEY,
    company_number VARCHAR NOT NULL,
    barcode VARCHAR,
    filing_type VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    subcategory VARCHAR,
    description VARCHAR NOT NULL,
    filed_on DATE NOT NULL,
    action_date DATE,
    pages INTEGER NOT NULL,
    paper_filed BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (company_number) REFERENCES company (company_number)
);

-- Scalar description_values. One row per key.
-- capital is a list and is stored in share_capital instead.
CREATE TABLE filing_attribute (
    transaction_id VARCHAR NOT NULL,
    attribute_name VARCHAR NOT NULL,
    attribute_value TEXT NOT NULL,
    PRIMARY KEY (transaction_id, attribute_name),
    FOREIGN KEY (transaction_id) REFERENCES filing (transaction_id)
);

CREATE TABLE filing_resolution (
    resolution_id INTEGER PRIMARY KEY,
    transaction_id VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    resolution_type VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    original_description VARCHAR,
    case_start_date DATE,
    resolution_date DATE,
    FOREIGN KEY (transaction_id) REFERENCES filing (transaction_id)
);

-- subcategory may be one string or a list. Each value is one row.
CREATE TABLE resolution_subcategory (
    resolution_id INTEGER NOT NULL,
    subcategory VARCHAR NOT NULL,
    PRIMARY KEY (resolution_id, subcategory),
    FOREIGN KEY (resolution_id) REFERENCES filing_resolution (resolution_id)
);

CREATE TABLE associated_filing (
    associated_filing_id INTEGER PRIMARY KEY,
    transaction_id VARCHAR NOT NULL,
    filing_type VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    filed_on DATE NOT NULL,
    action_date DATE,
    FOREIGN KEY (transaction_id) REFERENCES filing (transaction_id)
);

CREATE TABLE associated_filing_attribute (
    associated_filing_id INTEGER NOT NULL,
    attribute_name VARCHAR NOT NULL,
    attribute_value TEXT NOT NULL,
    PRIMARY KEY (associated_filing_id, attribute_name),
    FOREIGN KEY (associated_filing_id) REFERENCES associated_filing (associated_filing_id)
);

CREATE TABLE share_capital (
    associated_filing_id INTEGER NOT NULL,
    currency VARCHAR NOT NULL,
    amount NUMERIC NOT NULL,
    PRIMARY KEY (associated_filing_id, currency),
    FOREIGN KEY (associated_filing_id) REFERENCES associated_filing (associated_filing_id)
);

CREATE TABLE charge (
    company_number VARCHAR NOT NULL,
    charge_number INTEGER NOT NULL,
    charge_code VARCHAR NOT NULL UNIQUE,
    status VARCHAR NOT NULL,
    classification_type VARCHAR NOT NULL,
    classification_description VARCHAR NOT NULL,
    created_on DATE NOT NULL,
    delivered_on DATE NOT NULL,
    contains_fixed_charge BOOLEAN NOT NULL,
    contains_floating_charge BOOLEAN NOT NULL,
    contains_negative_pledge BOOLEAN NOT NULL,
    floating_charge_covers_all BOOLEAN NOT NULL,
    particulars_description TEXT NOT NULL,
    PRIMARY KEY (company_number, charge_number),
    FOREIGN KEY (company_number) REFERENCES company (company_number)
);

CREATE TABLE charge_person_entitled (
    company_number VARCHAR NOT NULL,
    charge_number INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    PRIMARY KEY (company_number, charge_number, name),
    FOREIGN KEY (company_number, charge_number) REFERENCES charge (company_number, charge_number)
);

CREATE TABLE charge_transaction (
    charge_transaction_id INTEGER PRIMARY KEY,
    company_number VARCHAR NOT NULL,
    charge_number INTEGER NOT NULL,
    delivered_on DATE NOT NULL,
    filing_type VARCHAR NOT NULL,
    filing_transaction_id VARCHAR,
    FOREIGN KEY (company_number, charge_number) REFERENCES charge (company_number, charge_number),
    FOREIGN KEY (filing_transaction_id) REFERENCES filing (transaction_id)
);

-- Derived metrics and labels. Blank failed_within_12m is stored as NULL.
-- status_today, accounts_type_last, and incorporated live on company.
CREATE TABLE company_snapshot (
    company_number VARCHAR PRIMARY KEY,
    as_of_date DATE NOT NULL,
    age_years NUMERIC NOT NULL,
    accounts_filings INTEGER NOT NULL,
    avg_days_late_accounts NUMERIC,
    max_days_late_accounts NUMERIC,
    days_since_last_accounts NUMERIC,
    directors_active INTEGER NOT NULL,
    director_resignations_12m INTEGER NOT NULL,
    director_appointments_12m INTEGER NOT NULL,
    address_changes INTEGER NOT NULL,
    strike_off_warnings INTEGER NOT NULL,
    charges_created INTEGER NOT NULL,
    charges_outstanding INTEGER NOT NULL,
    filings_total INTEGER NOT NULL,
    outcome VARCHAR NOT NULL CHECK (outcome IN ('active', 'insolvency', 'voluntary_strike_off')),
    outcome_date DATE NOT NULL,
    failed_within_12m BOOLEAN,
    FOREIGN KEY (company_number) REFERENCES company (company_number)
);

CREATE INDEX idx_officer_appointment_company ON officer_appointment (company_number);
CREATE INDEX idx_officer_appointment_person ON officer_appointment (officer_id);
CREATE INDEX idx_filing_company ON filing (company_number);
CREATE INDEX idx_filing_resolution_filing ON filing_resolution (transaction_id);
CREATE INDEX idx_associated_filing_filing ON associated_filing (transaction_id);
CREATE INDEX idx_charge_transaction_charge ON charge_transaction (company_number, charge_number);
CREATE INDEX idx_charge_transaction_filing ON charge_transaction (filing_transaction_id);
