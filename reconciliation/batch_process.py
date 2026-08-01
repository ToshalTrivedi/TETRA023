"""
Batch Invoice Processor
--------------------------
Reads every PDF/image invoice sitting in data/sample_invoices/, extracts
fields from each, runs reconciliation + auto-approval, and prints results.

Just drop invoice files into data/sample_invoices/ and run this script —
no manual file picking needed.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "extraction"))

from engine import ReconciliationEngine, exceptions_to_dataframe
from extract import extract_invoice

LOW_RISK_MAX_SCORE = 50
INVOICE_FOLDER = Path(__file__).parent.parent / "data" / "sample_invoices"


def extract_all_invoices(folder: Path) -> pd.DataFrame:
    """Extracts fields from every PDF/image file in the given folder."""
    rows = []
    supported_ext = (".pdf", ".jpg", ".jpeg", ".png")

    files = [f for f in folder.glob("*") if f.suffix.lower() in supported_ext]

    if not files:
        print(f"No invoice files found in {folder}")
        return pd.DataFrame()

    for file_path in files:
        print(f"Extracting: {file_path.name} ...")
        result = extract_invoice(str(file_path))

        if "error" in result:
            print(f"  Failed: {result['error']}")
            continue

        rows.append({
            "invoice_number": result.get("invoice_number"),
            "vendor_name": result.get("vendor_name"),
            "invoice_date": result.get("invoice_date"),
            "taxable_value": result.get("taxable_value"),
            "tax_amount": result.get("tax_amount"),
            "total_amount": result.get("total_amount"),
            "gstin": result.get("gstin"),
            "source_file": file_path.name,
        })

    return pd.DataFrame(rows)


def classify_invoices(invoices_df: pd.DataFrame, exceptions_df: pd.DataFrame) -> pd.DataFrame:
    if not exceptions_df.empty:
        max_risk_per_invoice = exceptions_df.groupby("Invoice #")["Risk Score"].max().to_dict()
        exception_count_per_invoice = exceptions_df.groupby("Invoice #").size().to_dict()
    else:
        max_risk_per_invoice = {}
        exception_count_per_invoice = {}

    rows = []
    for _, inv in invoices_df.iterrows():
        inv_num = inv["invoice_number"]
        risk_score = max_risk_per_invoice.get(inv_num, 0)
        exception_count = exception_count_per_invoice.get(inv_num, 0)

        if exception_count == 0:
            decision, confidence = "AUTO-APPROVE", 98
        elif risk_score <= LOW_RISK_MAX_SCORE:
            decision, confidence = "LOW-RISK REVIEW", 100 - risk_score
        else:
            decision, confidence = "MANUAL REVIEW REQUIRED", 100 - risk_score

        rows.append({
            "Invoice #": inv_num,
            "Vendor": inv["vendor_name"],
            "Decision": decision,
            "Confidence %": confidence,
            "Risk Score": risk_score,
            "Exception Count": exception_count,
        })

    return pd.DataFrame(rows)


def workload_summary(decision_df: pd.DataFrame) -> dict:
    total = len(decision_df)
    manual_required = len(decision_df[decision_df["Decision"] == "MANUAL REVIEW REQUIRED"])
    workload_reduction_pct = ((total - manual_required) / total * 100) if total > 0 else 0

    return {
        "total_invoices": total,
        "needs_full_review": manual_required,
        "workload_reduction_pct": round(workload_reduction_pct, 1),
        "headline": (
            f"Reduced manual review from {total} invoices to {manual_required} "
            f"— a {workload_reduction_pct:.0f}% workload reduction."
        ),
    }


if __name__ == "__main__":
    print("=" * 60)
    print(f"Batch processing invoices from: {INVOICE_FOLDER}")
    print("=" * 60)

    if not INVOICE_FOLDER.exists():
        print(f"Folder not found: {INVOICE_FOLDER}")
        print("Create it and add your PDF/image invoices there first.")
        sys.exit(1)

    invoices = extract_all_invoices(INVOICE_FOLDER)

    if invoices.empty:
        print("No invoices extracted. Exiting.")
        sys.exit(0)

    data_dir = Path(__file__).parent.parent / "data"
    ledger = pd.read_csv(data_dir / "purchase_ledger.csv")
    vendors = pd.read_csv(data_dir / "vendor_master.csv")

    engine = ReconciliationEngine(ledger, vendors)
    exceptions = engine.run(invoices)
    exceptions_df = exceptions_to_dataframe(exceptions)

    decision_df = classify_invoices(invoices, exceptions_df)
    summary = workload_summary(decision_df)

    pd.set_option("display.max_colwidth", None)
    print("\n" + decision_df.to_string(index=False))
    print("\n" + "=" * 60)
    print(summary["headline"])
    print("=" * 60)
    

    