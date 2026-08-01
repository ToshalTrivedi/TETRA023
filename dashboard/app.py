"""
Invoice Risk Screening Dashboard
----------------------------------
Streamlit app: upload/point to invoices, ledger, vendor master -> see a
prioritized exception dashboard with risk scores, explanations, and a
searchable audit trail.

Run with: streamlit run app.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "reconciliation"))

import pandas as pd
import streamlit as st
from engine import ReconciliationEngine, exceptions_to_dataframe

st.set_page_config(page_title="Invoice Risk Screening", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"

st.title("Invoice Risk Screening Dashboard")
st.caption("AI-powered reconciliation of invoices against purchase ledger & vendor master")

# ---------------- Load data ----------------
with st.sidebar:
    st.header("Data Sources")
    use_sample = st.checkbox("Use sample/demo data", value=True)

    if use_sample:
        ledger = pd.read_csv(DATA_DIR / "purchase_ledger.csv")
        vendors = pd.read_csv(DATA_DIR / "vendor_master.csv")
        invoices = pd.read_csv(DATA_DIR / "extracted_invoices.csv")
    else:
        ledger_file = st.file_uploader("Purchase Ledger (CSV)", type="csv")
        vendor_file = st.file_uploader("Vendor Master (CSV)", type="csv")
        invoice_file = st.file_uploader("Extracted Invoices (CSV)", type="csv")
        if not (ledger_file and vendor_file and invoice_file):
            st.info("Upload all three files, or check 'Use sample data' above.")
            st.stop()
        ledger = pd.read_csv(ledger_file)
        vendors = pd.read_csv(vendor_file)
        invoices = pd.read_csv(invoice_file)

# ---------------- Run engine ----------------
engine = ReconciliationEngine(ledger, vendors)
exceptions = engine.run(invoices)
exceptions_df = exceptions_to_dataframe(exceptions)

flagged_invoice_numbers = set(exceptions_df["Invoice #"].unique())
total_invoices = invoices["invoice_number"].nunique()
clean_count = total_invoices - len(flagged_invoice_numbers)
workload_reduction = (clean_count / total_invoices * 100) if total_invoices else 0

# ---------------- Top metrics ----------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Invoices Processed", total_invoices)
col2.metric("Clean (Auto-Cleared)", clean_count)
col3.metric("Flagged for Review", len(flagged_invoice_numbers))
col4.metric("Manual Review Workload Reduced", f"{workload_reduction:.0f}%")

st.divider()

# ---------------- Exception dashboard ----------------
st.subheader("Prioritized Exception Dashboard")

col_a, col_b, col_c = st.columns(3)
with col_a:
    min_risk = st.slider("Minimum risk score", 0, 100, 0)
with col_b:
    types = ["All"] + sorted(exceptions_df["Exception Type"].unique().tolist()) if not exceptions_df.empty else ["All"]
    type_filter = st.selectbox("Exception type", types)
with col_c:
    search = st.text_input("Search invoice # / vendor")

filtered = exceptions_df.copy()
if not filtered.empty:
    filtered = filtered[filtered["Risk Score"] >= min_risk]
    if type_filter != "All":
        filtered = filtered[filtered["Exception Type"] == type_filter]
    if search:
        mask = (
            filtered["Invoice #"].str.contains(search, case=False, na=False)
            | filtered["Vendor"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]


def risk_badge(score):
    if score >= 80:
        return "🔴 High"
    elif score >= 50:
        return "🟠 Medium"
    else:
        return "🟡 Low"


if filtered.empty:
    st.success("No exceptions match the current filter. ✅")
else:
    display_df = filtered.copy()
    display_df.insert(0, "Risk Level", display_df["Risk Score"].apply(risk_badge))
    st.dataframe(
        display_df[["Risk Level", "Risk Score", "Invoice #", "Vendor", "Exception Type", "Explanation", "Source File"]],
        use_container_width=True,
        hide_index=True,
        height=400,
    )

st.divider()

# ---------------- Audit trail detail view ----------------
st.subheader("Audit Trail — Invoice Detail Lookup")
invoice_lookup = st.selectbox(
    "Select an invoice to see full audit trail",
    options=["-- Select --"] + sorted(invoices["invoice_number"].unique().tolist()),
)

if invoice_lookup != "-- Select --":
    inv_rows = invoices[invoices["invoice_number"] == invoice_lookup]
    exc_rows = exceptions_df[exceptions_df["Invoice #"] == invoice_lookup]
    ledger_rows = ledger[ledger["invoice_number"] == invoice_lookup]

    st.markdown(f"### 📄 {invoice_lookup}")
    left, right = st.columns(2)
    with left:
        st.markdown("**Extracted Invoice Data**")
        st.dataframe(inv_rows.T.rename(columns={inv_rows.index[0]: "Value"}), use_container_width=True)
    with right:
        st.markdown("**Matching Ledger Entry**")
        if ledger_rows.empty:
            st.warning("No matching ledger entry found.")
        else:
            st.dataframe(ledger_rows.T.rename(columns={ledger_rows.index[0]: "Value"}), use_container_width=True)

    if not exc_rows.empty:
        st.markdown("**⚠️ Exceptions Raised**")
        for _, row in exc_rows.iterrows():
            st.error(f"**{row['Exception Type']}** (Risk: {row['Risk Score']}/100)\n\n{row['Explanation']}")
    else:
        st.success("No exceptions raised for this invoice. ✅")

st.divider()
st.caption("Prototype for Indo-French AI Innovation Sprint — Invoice Risk Screening Module")
