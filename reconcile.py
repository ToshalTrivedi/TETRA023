"""
reconcile.py
------------
Takes a batch of extracted invoices + a purchase ledger, and produces
a prioritized exception list: duplicates, missing ledger entries,
amount/date mismatches, invalid GSTINs, and unusual vendor activity.

Every exception keeps a pointer back to the source invoice file (the
"audit trail" requirement) and gets a 0-100 risk score.
"""

from collections import Counter
from difflib import SequenceMatcher

import pandas as pd

from gstin_verify import is_valid_gstin_format

# How much each issue contributes to the risk score. Tune these based
# on what your audit team actually cares about most.
RISK_WEIGHTS = {
    "duplicate_invoice": 40,
    "missing_in_ledger": 25,
    "amount_mismatch": 30,
    "date_mismatch": 10,
    "invalid_gstin_format": 35,
    "gstin_inactive": 30,
    "vendor_name_mismatch": 15,
    "new_vendor_not_in_master": 10,
}

AMOUNT_TOLERANCE = 1.0  # rupees - allows for rounding differences


def _name_similarity(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _find_ledger_match(invoice, ledger_df):
    """Match on invoice_number (+ gstin if available). Returns the
    matching ledger row (as a dict) or None."""
    candidates = ledger_df[ledger_df["invoice_number"] == invoice["invoice_number"]]
    if invoice.get("gstin"):
        gstin_match = candidates[candidates["gstin"] == invoice["gstin"]]
        if not gstin_match.empty:
            candidates = gstin_match
    if candidates.empty:
        return None
    return candidates.iloc[0].to_dict()


def reconcile(invoices, ledger_df, vendor_master_df=None, gstin_lookup=None):
    """
    invoices: list of dicts from extract_invoice.extract_invoice_fields()
    ledger_df: pandas DataFrame with columns
        invoice_number, vendor_name, gstin, date, taxable_value,
        tax_amount, total_amount
    vendor_master_df: optional DataFrame with a 'gstin' column of known
        approved vendors, used for the "new/unknown vendor" check
    gstin_lookup: optional dict {gstin: result_from_SandboxGSTINClient}
        pre-fetched GSTIN verification results, to avoid re-hitting the
        API for every invoice

    Returns a pandas DataFrame of exceptions, one row per issue found,
    sorted by risk_score descending.
    """
    gstin_lookup = gstin_lookup or {}

    # Duplicate detection across the current invoice batch itself
    invoice_keys = [(inv.get("invoice_number"), inv.get("gstin")) for inv in invoices]
    key_counts = Counter(k for k in invoice_keys if k[0] and k[1])

    exceptions = []

    for inv in invoices:
        issues = []
        details = []

        key = (inv.get("invoice_number"), inv.get("gstin"))
        if key[0] and key[1] and key_counts[key] > 1:
            issues.append("duplicate_invoice")
            details.append(f"Invoice {key[0]} for GSTIN {key[1]} appears {key_counts[key]}x in this batch")

        if not inv.get("gstin"):
            issues.append("invalid_gstin_format")
            details.append("No GSTIN could be extracted from the document")
        elif not is_valid_gstin_format(inv["gstin"]):
            issues.append("invalid_gstin_format")
            details.append(f"GSTIN '{inv['gstin']}' fails checksum/format pattern")
        else:
            verify = gstin_lookup.get(inv["gstin"])
            if verify and verify.get("ok") and verify.get("status") not in (None, "Active"):
                issues.append("gstin_inactive")
                details.append(f"GSTIN status is '{verify.get('status')}', not Active")

        ledger_row = _find_ledger_match(inv, ledger_df) if inv.get("invoice_number") else None

        if ledger_row is None:
            issues.append("missing_in_ledger")
            details.append("No matching invoice_number/GSTIN found in the purchase ledger")
        else:
            if inv.get("total_amount") is not None and ledger_row.get("total_amount") is not None:
                if abs(inv["total_amount"] - ledger_row["total_amount"]) > AMOUNT_TOLERANCE:
                    issues.append("amount_mismatch")
                    details.append(
                        f"Invoice total {inv['total_amount']} vs ledger total {ledger_row['total_amount']}"
                    )
            if inv.get("date") and ledger_row.get("date") and inv["date"] != ledger_row["date"]:
                issues.append("date_mismatch")
                details.append(f"Invoice date {inv['date']} vs ledger date {ledger_row['date']}")

            sim = _name_similarity(inv.get("vendor_name"), ledger_row.get("vendor_name"))
            if inv.get("vendor_name") and ledger_row.get("vendor_name") and sim < 0.6:
                issues.append("vendor_name_mismatch")
                details.append(
                    f"Extracted vendor '{inv.get('vendor_name')}' vs ledger vendor '{ledger_row.get('vendor_name')}' (similarity {sim:.2f})"
                )

        if vendor_master_df is not None and inv.get("gstin"):
            known = vendor_master_df["gstin"].astype(str).str.upper().tolist()
            if inv["gstin"].upper() not in known:
                issues.append("new_vendor_not_in_master")
                details.append(f"GSTIN {inv['gstin']} not present in the approved vendor master")

        if not issues:
            continue  # clean invoice, nothing to flag

        risk_score = min(100, sum(RISK_WEIGHTS.get(i, 5) for i in issues))

        exceptions.append({
            "source_file": inv.get("source_file"),
            "invoice_number": inv.get("invoice_number"),
            "vendor_name": inv.get("vendor_name"),
            "gstin": inv.get("gstin"),
            "total_amount": inv.get("total_amount"),
            "issues": ", ".join(issues),
            "details": " | ".join(details),
            "risk_score": risk_score,
        })

    df = pd.DataFrame(exceptions)
    if not df.empty:
        df = df.sort_values("risk_score", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    # Tiny smoke test with synthetic data - no files or network needed.
    invoices = [
        {
            "source_file": "invoice_101.pdf",
            "invoice_number": "INV-101",
            "vendor_name": "Vicky Pvt Ltd",
            "gstin": "29AFSPB9500E1ZY",
            "date": "18/06/2026",
            "total_amount": 11800.0,
        },
        {
            "source_file": "invoice_101_dup.pdf",
            "invoice_number": "INV-101",
            "vendor_name": "Vicky Pvt Ltd",
            "gstin": "29AFSPB9500E1ZY",
            "date": "18/06/2026",
            "total_amount": 11800.0,
        },
        {
            "source_file": "invoice_102.pdf",
            "invoice_number": "INV-102",
            "vendor_name": "Acme Traders",
            "gstin": "BADGSTIN123",
            "date": "20/06/2026",
            "total_amount": 5000.0,
        },
    ]
    ledger = pd.DataFrame([
        {
            "invoice_number": "INV-101",
            "vendor_name": "Vicky Pvt Ltd",
            "gstin": "29AFSPB9500E1ZY",
            "date": "18/06/2026",
            "taxable_value": 10000.0,
            "tax_amount": 1800.0,
            "total_amount": 11800.0,
        },
    ])

    result = reconcile(invoices, ledger)
    print(result.to_string(index=False))
