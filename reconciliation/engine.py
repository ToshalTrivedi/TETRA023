"""
Reconciliation & Risk Scoring Engine
--------------------------------------
Compares extracted invoices against the purchase ledger and vendor master.
Detects: duplicates, near-duplicates, missing ledger records, amount/date
mismatches, invalid/mismatched GSTINs, and unusual vendor activity spikes.

Every exception gets:
- a risk score (0-100)
- a plain-English explanation of WHY (so it's auditable, not a black box)
- a link back to the source invoice file

Design choice: rule-based + statistical baselining instead of a trained ML
model. This is deliberate — with synthetic/limited hackathon data, a rule
engine is more accurate, fully explainable (critical for audit use cases),
and doesn't require labeled training data we don't have.
"""

from dataclasses import dataclass, field

import pandas as pd
from rapidfuzz import fuzz

from gstin_utils import validate_gstin_full


@dataclass
class Exception_:
    invoice_number: str
    source_file: str
    vendor_name: str
    exception_type: str
    risk_score: int
    reasons: list = field(default_factory=list)  # list of (reason_text, weight)

    def explanation(self) -> str:
        parts = [f"{reason} (+{weight})" for reason, weight in self.reasons]
        return " | ".join(parts)


class ReconciliationEngine:
    def __init__(self, ledger_df: pd.DataFrame, vendor_df: pd.DataFrame):
        self.ledger = ledger_df.copy()
        self.vendors = vendor_df.copy()

    # ---------- individual checks ----------

    def _exact_duplicate_check(self, invoices_df: pd.DataFrame) -> dict:
        """Flags invoices with the exact same invoice_number appearing more than once."""
        counts = invoices_df["invoice_number"].value_counts()
        return {num: cnt for num, cnt in counts.items() if cnt > 1}

    def _near_duplicate_check(self, invoices_df: pd.DataFrame, threshold: int = 90) -> list:
        """
        Catches near-duplicates: same vendor+amount+date but invoice number
        altered slightly (e.g. INV-2024-0451 vs INV-2024-0451A).
        Uses fuzzy string matching (token-based Levenshtein-style similarity).
        """
        flagged_pairs = []
        rows = invoices_df.to_dict("records")
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                if a["invoice_number"] == b["invoice_number"]:
                    continue  # handled by exact duplicate check
                same_vendor = a["vendor_name"] == b["vendor_name"]
                same_amount = abs(float(a["total_amount"]) - float(b["total_amount"])) < 1
                same_date = a["invoice_date"] == b["invoice_date"]
                num_similarity = fuzz.ratio(str(a["invoice_number"]), str(b["invoice_number"]))
                if same_vendor and same_amount and same_date and num_similarity >= threshold:
                    flagged_pairs.append((a, b, num_similarity))
        return flagged_pairs

    def _vendor_activity_baseline(self, vendor_name: str, invoice_amount: float) -> tuple:
        """Compares an invoice amount to the vendor's typical monthly volume."""
        vendor_row = self.vendors[self.vendors["vendor_name"] == vendor_name]
        if vendor_row.empty:
            return False, None
        avg = float(vendor_row.iloc[0]["avg_monthly_amount"])
        is_unusual = invoice_amount > avg * 1.5  # >50% above baseline = flag
        return is_unusual, avg

    # ---------- main run ----------

    def run(self, invoices_df: pd.DataFrame) -> list[Exception_]:
        exceptions = []

        # 1. Exact duplicates
        dup_counts = self._exact_duplicate_check(invoices_df)
        seen_dupes = set()
        for _, inv in invoices_df.iterrows():
            if inv["invoice_number"] in dup_counts and inv["invoice_number"] not in seen_dupes:
                seen_dupes.add(inv["invoice_number"])
                dupes = invoices_df[invoices_df["invoice_number"] == inv["invoice_number"]]
                for _, d in dupes.iterrows():
                    exceptions.append(Exception_(
                        invoice_number=d["invoice_number"],
                        source_file=d["source_file"],
                        vendor_name=d["vendor_name"],
                        exception_type="Duplicate Invoice",
                        risk_score=90,
                        reasons=[(f"Invoice number appears {dup_counts[inv['invoice_number']]} times across submitted documents", 90)],
                    ))

        # 2. Near-duplicates (fuzzy)
        for a, b, similarity in self._near_duplicate_check(invoices_df):
            exceptions.append(Exception_(
                invoice_number=b["invoice_number"],
                source_file=b["source_file"],
                vendor_name=b["vendor_name"],
                exception_type="Near-Duplicate Invoice",
                risk_score=80,
                reasons=[(f"{similarity:.0f}% similar to invoice {a['invoice_number']} ({a['source_file']}) — same vendor, amount, and date", 80)],
            ))

        # 3. Per-invoice checks: ledger match, amount/date mismatch, GSTIN, vendor spike
        for _, inv in invoices_df.iterrows():
            reasons = []
            risk = 0

            ledger_match = self.ledger[self.ledger["invoice_number"] == inv["invoice_number"]]

            if ledger_match.empty:
                reasons.append(("No matching entry found in purchase ledger", 60))
                risk += 60
            else:
                led = ledger_match.iloc[0]
                if abs(float(led["total_amount"]) - float(inv["total_amount"])) > 1:
                    diff = float(inv["total_amount"]) - float(led["total_amount"])
                    reasons.append((f"Total amount mismatch vs ledger: invoice ₹{inv['total_amount']} vs ledger ₹{led['total_amount']} (diff ₹{diff:+.0f})", 50))
                    risk += 50
                if str(led["invoice_date"]) != str(inv["invoice_date"]):
                    reasons.append((f"Date mismatch vs ledger: invoice {inv['invoice_date']} vs ledger {led['invoice_date']}", 30))
                    risk += 30
                if str(led["gstin"]).upper() != str(inv["gstin"]).upper():
                    reasons.append(("GSTIN on invoice does not match GSTIN recorded in ledger for this vendor", 55))
                    risk += 55

            # GSTIN format + state cross-check
            vendor_row = self.vendors[self.vendors["vendor_name"] == inv["vendor_name"]]
            expected_state = vendor_row.iloc[0]["state"] if not vendor_row.empty else None
            gstin_report = validate_gstin_full(inv["gstin"], expected_state)

            if not gstin_report["format_valid"]:
                reasons.append((f"GSTIN '{inv['gstin']}' does not match valid GST format", 70))
                risk += 70
            elif expected_state and gstin_report["state_match"] is False:
                reasons.append((f"GSTIN state code ({gstin_report['state_from_gstin']}) does not match vendor's registered state ({expected_state}) — possible cloned/incorrect GSTIN", 65))
                risk += 65

            if vendor_row.empty:
                reasons.append(("Vendor not found in Vendor Master — unsupported/unrecognized vendor", 75))
                risk += 75
            else:
                is_unusual, avg = self._vendor_activity_baseline(inv["vendor_name"], float(inv["total_amount"]))
                if is_unusual:
                    reasons.append((f"Invoice amount ₹{inv['total_amount']:.0f} is {(float(inv['total_amount'])/avg - 1)*100:.0f}% above vendor's average monthly volume (₹{avg:.0f})", 40))
                    risk += 40

            if reasons:
                exception_type = reasons[0][0].split(":")[0] if len(reasons) == 1 else "Multiple Exceptions"
                exceptions.append(Exception_(
                    invoice_number=inv["invoice_number"],
                    source_file=inv["source_file"],
                    vendor_name=inv["vendor_name"],
                    exception_type=exception_type,
                    risk_score=min(risk, 100),
                    reasons=reasons,
                ))

        return exceptions


def exceptions_to_dataframe(exceptions: list[Exception_]) -> pd.DataFrame:
    rows = []
    for e in exceptions:
        rows.append({
            "Invoice #": e.invoice_number,
            "Source File": e.source_file,
            "Vendor": e.vendor_name,
            "Exception Type": e.exception_type,
            "Risk Score": e.risk_score,
            "Explanation": e.explanation(),
        })
    df = pd.DataFrame(rows).sort_values("Risk Score", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    ledger = pd.read_csv("../data/purchase_ledger.csv")
    vendors = pd.read_csv("../data/vendor_master.csv")
    invoices = pd.read_csv("../data/extracted_invoices.csv")

    engine = ReconciliationEngine(ledger, vendors)
    exceptions = engine.run(invoices)
    df = exceptions_to_dataframe(exceptions)
    pd.set_option("display.max_colwidth", None)
    print(df.to_string())
    print(f"\nTotal invoices: {len(invoices)} | Flagged: {df['Invoice #'].nunique()} | Clean: {len(invoices) - df['Invoice #'].nunique()}")
