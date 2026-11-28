"""Fitted v1 decision tree, exported as plain if/else rules.

GENERATED FILE - do not edit by hand.
Source: PIPAIF26_Team1_Model_v1 / export_tree_rules.py
Tree: gini, max_depth=12, min_samples_leaf=5, min_samples_split=10
Leaves: 62, depth: 12
Held-out test accuracy: 65.8% (always-"active" baseline: 58.7%)

Possible outputs: active, compulsory_strike_off, insolvency, voluntary_strike_off
"""


def _le(c, name, threshold, missing_goes_left):
    """True when c[name] <= threshold. Missing values follow the fitted tree."""
    value = c.get(name)
    if value is None:
        return missing_goes_left
    value = float(value)
    if value != value:  # NaN
        return missing_goes_left
    return value <= threshold


def predict_outcome(c):
    """Return the predicted final_outcome for one company.

    c is a dict with these keys (numbers may be None when unknown):
      age_years
      accounts_filings
      avg_days_late_accounts
      max_days_late_accounts
      days_since_last_accounts
      directors_active
      director_resignations_12m
      director_appointments_12m
      address_changes
      strike_off_warnings
      charges_created
      charges_outstanding
      filings_total
      n_sic_codes
    and these text keys (use "none" for an empty SIC slot,
    "no_accounts" when no accounts have been filed):
      sic_1
      sic_2
      sic_3
      sic_4
      jurisdiction
      last_accounts_type
    """
    if _le(c, "accounts_filings", 8.5, True):
        if _le(c, "strike_off_warnings", 0.5, True):
            if c.get("sic_1") != "56101":
                if _le(c, "avg_days_late_accounts", -8.650000095367432, True):
                    if _le(c, "n_sic_codes", 3.5, True):
                        if _le(c, "accounts_filings", 4.5, True):
                            if c.get("last_accounts_type") != "micro-entity":
                                if _le(c, "age_years", 1.4500000476837158, False):
                                    return "active"
                                else:
                                    if _le(c, "days_since_last_accounts", 238.0, True):
                                        if _le(c, "age_years", 1.6399999856948853, False):
                                            return "compulsory_strike_off"
                                        else:
                                            if _le(c, "n_sic_codes", 1.5, True):
                                                return "voluntary_strike_off"
                                            else:
                                                return "active"
                                    else:
                                        return "compulsory_strike_off"
                            else:
                                if _le(c, "age_years", 2.680000066757202, False):
                                    if _le(c, "days_since_last_accounts", 135.5, False):
                                        return "active"
                                    else:
                                        return "active"
                                else:
                                    if _le(c, "days_since_last_accounts", 281.5, False):
                                        return "compulsory_strike_off"
                                    else:
                                        return "insolvency"
                        else:
                            return "insolvency"
                    else:
                        return "active"
                else:
                    if _le(c, "address_changes", 1.5, True):
                        if _le(c, "filings_total", 8.5, False):
                            if _le(c, "age_years", 2.2950000762939453, False):
                                return "active"
                            else:
                                return "compulsory_strike_off"
                        else:
                            if _le(c, "filings_total", 18.0, True):
                                return "active"
                            else:
                                return "active"
                    else:
                        return "voluntary_strike_off"
            else:
                if _le(c, "charges_created", 0.5, True):
                    if _le(c, "days_since_last_accounts", 78.5, False):
                        if _le(c, "age_years", 4.944999933242798, True):
                            if _le(c, "avg_days_late_accounts", 87.75, True):
                                return "active"
                            else:
                                return "active"
                        else:
                            return "active"
                    else:
                        if _le(c, "days_since_last_accounts", 109.0, False):
                            if _le(c, "max_days_late_accounts", 72.5, False):
                                return "active"
                            else:
                                if _le(c, "avg_days_late_accounts", 86.5, True):
                                    return "insolvency"
                                else:
                                    return "insolvency"
                        else:
                            if _le(c, "max_days_late_accounts", -168.5, False):
                                return "insolvency"
                            else:
                                if _le(c, "directors_active", 1.5, True):
                                    if _le(c, "filings_total", 4.5, False):
                                        if _le(c, "age_years", 1.4950000047683716, False):
                                            return "active"
                                        else:
                                            if c.get("jurisdiction") != "england-wales":
                                                return "active"
                                            else:
                                                if _le(c, "age_years", 1.6549999713897705, False):
                                                    return "insolvency"
                                                else:
                                                    return "compulsory_strike_off"
                                    else:
                                        if _le(c, "days_since_last_accounts", 305.0, True):
                                            if _le(c, "max_days_late_accounts", 133.5, False):
                                                return "active"
                                            else:
                                                if _le(c, "director_resignations_12m", 0.5, True):
                                                    return "active"
                                                else:
                                                    return "active"
                                        else:
                                            if _le(c, "max_days_late_accounts", -20.5, True):
                                                return "active"
                                            else:
                                                return "active"
                                else:
                                    if _le(c, "max_days_late_accounts", -6.0, False):
                                        if _le(c, "avg_days_late_accounts", -72.1500015258789, False):
                                            return "active"
                                        else:
                                            return "active"
                                    else:
                                        if _le(c, "days_since_last_accounts", 306.0, True):
                                            if _le(c, "avg_days_late_accounts", 7.75, True):
                                                if _le(c, "max_days_late_accounts", float("inf"), False):
                                                    return "insolvency"
                                                else:
                                                    return "insolvency"
                                            else:
                                                return "compulsory_strike_off"
                                        else:
                                            return "active"
                else:
                    if _le(c, "charges_outstanding", 1.5, True):
                        if _le(c, "age_years", 3.309999942779541, False):
                            return "insolvency"
                        else:
                            return "insolvency"
                    else:
                        return "active"
        else:
            if _le(c, "accounts_filings", 4.5, True):
                if c.get("last_accounts_type") != "dormant":
                    if _le(c, "days_since_last_accounts", 50.0, False):
                        return "active"
                    else:
                        if _le(c, "age_years", 3.375, False):
                            if _le(c, "days_since_last_accounts", 357.5, True):
                                if _le(c, "filings_total", 6.5, True):
                                    if _le(c, "age_years", 2.5600000619888306, True):
                                        if _le(c, "age_years", 1.824999988079071, False):
                                            return "active"
                                        else:
                                            return "active"
                                    else:
                                        return "active"
                                else:
                                    if c.get("last_accounts_type") != "micro-entity":
                                        return "active"
                                    else:
                                        return "active"
                            else:
                                return "active"
                        else:
                            if _le(c, "days_since_last_accounts", 880.0, False):
                                if _le(c, "accounts_filings", 3.5, True):
                                    if _le(c, "days_since_last_accounts", 690.0, True):
                                        if _le(c, "avg_days_late_accounts", 74.3499984741211, True):
                                            return "active"
                                        else:
                                            return "active"
                                    else:
                                        if _le(c, "age_years", 4.869999885559082, True):
                                            return "active"
                                        else:
                                            return "active"
                                else:
                                    return "active"
                            else:
                                return "active"
                else:
                    if _le(c, "filings_total", 17.0, True):
                        return "compulsory_strike_off"
                    else:
                        return "active"
            else:
                if _le(c, "max_days_late_accounts", 75.5, False):
                    return "active"
                else:
                    if _le(c, "age_years", 6.639999866485596, False):
                        return "active"
                    else:
                        if _le(c, "avg_days_late_accounts", 44.29999923706055, True):
                            return "insolvency"
                        else:
                            return "insolvency"
    else:
        if _le(c, "max_days_late_accounts", 30.5, False):
            return "insolvency"
        else:
            return "insolvency"
