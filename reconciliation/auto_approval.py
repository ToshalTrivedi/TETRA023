"""
Confidence-Weighted Auto-Approval Engine
-------------------------------------------
Instead of just flagging problems, this module classifies every invoice
into a decision bucket:

  - AUTO-APPROVE : high confidence, zero exceptions -> skip manual review
  - LOW-RISK REVIEW : minor exceptions, low risk score -> quick check
  - MANUAL REVIEW REQUIRED : high risk score or critical exception -> full audit

This reframes the tool from "we found problems" to "we tell you exactly
which invoices you can SKIP reviewing" — the actual ROI auditors care about.

Depends on: reconciliation/engine.py (ReconciliationEngine, exceptions_to_dataframe)
"""

import pandas as pd

# Thresholds - tune these based on your risk appetite
AUTO_APPROVE_MAX_RISK = 0        # 0 exceptions = auto-approve
LOW_RISK_MAX_SCORE = 50          # risk score below this = quick review only
# anything above LOW_RISK_MAX_SCORE = manual review required


def classify_invoices(invoices_df: pd.DataFrame, exceptions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes the full invoice list + exceptions dataframe (from engine.run())
    and returns a per-invoice decision table with auto-approval status.
    """
    if not exceptions_df.empty:
        max_risk_per_invoice = (
            exceptions_df.groupby("Invoice #")["Risk Score"].max().to_dict()
        )
        exception_count_per_invoice = (
            exceptions_df.groupby("Invoice #").size().to_dict()
        )
    else:
        max_risk_per_invoice = {}
        exception_count_per_invoice = {}

    rows = []
    for _, inv in invoices_df.iterrows():
        inv_num = inv["invoice_number"]
        risk_score = max_risk_per_invoice.get(inv_num, 0)
        exception_count = exception_count_per_invoice.get(inv_num, 0)

        if exception_count == 0:
            decision = "AUTO-APPROVE"
            confidence = 98
        elif risk_score <= LOW_RISK_MAX_SCORE:
            decision = "LOW-RISK REVIEW"
            confidence = 100 - risk_score
        else:
            decision = "MANUAL REVIEW REQUIRED"
            confidence = 100 - risk_score

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
    """
    Produces the headline ROI numbers for the pitch:
    'Reduced manual review from X invoices to Y — a Z% workload reduction.'
    """
    total = len(decision_df)
    auto_approved = len(decision_df[decision_df["Decision"] == "AUTO-APPROVE"])
    low_risk = len(decision_df[decision_df["Decision"] == "LOW-RISK REVIEW"])
    manual_required = len(decision_df[decision_df["Decision"] == "MANUAL REVIEW REQUIRED"])

    needs_full_review = manual_required
    workload_reduction_pct = (
        ((total - needs_full_review) / total * 100) if total > 0 else 0
    )

    return {
        "total_invoices": total,
        "auto_approved": auto_approved,
        "low_risk_review": low_risk,
        "manual_review_required": manual_required,
        "needs_full_review": needs_full_review,
        "workload_reduction_pct": round(workload_reduction_pct, 1),
        "headline": (
            f"Reduced manual review from {total} invoices to {needs_full_review} "
            f"— a {workload_reduction_pct:.0f}% workload reduction."
        ),
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent))
    from engine import ReconciliationEngine, exceptions_to_dataframe

    ledger = pd.read_csv("../data/purchase_ledger.csv")
    vendors = pd.read_csv("../data/vendor_master.csv")
    invoices = pd.read_csv("../data/extracted_invoices.csv")

    engine = ReconciliationEngine(ledger, vendors)
    exceptions = engine.run(invoices)
    exceptions_df = exceptions_to_dataframe(exceptions)

    decision_df = classify_invoices(invoices, exceptions_df)
    summary = workload_summary(decision_df)

    pd.set_option("display.max_colwidth", None)
    print(decision_df.to_string(index=False))
    print("\n" + "=" * 60)
    print(summary["headline"])
    print("=" * 60)


    