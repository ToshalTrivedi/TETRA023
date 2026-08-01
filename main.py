"""
main.py
-------
End-to-end pipeline for the hackathon prototype:

    invoices (PDF/image folder) --> extract_invoice.py --> fields
    fields[gstin]              --> gstin_verify.py      --> live status
    fields + ledger.csv        --> reconcile.py          --> exceptions
    exceptions                 --> exceptions.csv + dashboard.html

Usage:
    # Real run against a folder of invoice files
    python main.py --invoices ./invoices --ledger ./ledger.csv \
        --vendor-master ./vendor_master.csv \
        --api-key YOUR_KEY --api-secret YOUR_SECRET

    # Quick demo with synthetic data (no OCR deps / API key needed)
    python main.py --demo
"""

import argparse
import glob
import os
from pathlib import Path

import pandas as pd

from extract_invoice import extract_invoice_fields
from gstin_verify import SandboxGSTINClient
from reconcile import reconcile

OUTPUT_DIR = "output"


def run_extraction(invoice_folder):
    files = []
    for ext in ("*.pdf", "*.png", "*.jpg", "*.jpeg"):
        files.extend(glob.glob(os.path.join(invoice_folder, ext)))

    invoices = []
    for f in sorted(files):
        try:
            invoices.append(extract_invoice_fields(f))
        except Exception as exc:
            invoices.append({"source_file": f, "extraction_error": str(exc)})
    return invoices


def run_gstin_verification(invoices, api_key, api_secret):
    if not api_key or not api_secret:
        print("No Sandbox API credentials given - skipping live GSTIN verification "
              "(format checks still run).")
        return {}

    client = SandboxGSTINClient(api_key=api_key, api_secret=api_secret)
    lookup = {}
    gstins = {inv["gstin"] for inv in invoices if inv.get("gstin")}
    for gstin in gstins:
        lookup[gstin] = client.search_gstin(gstin)
    return lookup


def build_dashboard_html(exceptions_df, output_path):
    def risk_color(score):
        if score >= 60:
            return "#e74c3c"   # high risk - red
        if score >= 30:
            return "#f39c12"   # medium risk - amber
        return "#f1c40f"       # low-ish risk - yellow

    rows_html = ""
    for _, row in exceptions_df.iterrows():
        color = risk_color(row["risk_score"])
        rows_html += f"""
        <tr>
          <td>{row['invoice_number'] or '-'}</td>
          <td>{row['vendor_name'] or '-'}</td>
          <td>{row['gstin'] or '-'}</td>
          <td>{row['total_amount'] if pd.notna(row['total_amount']) else '-'}</td>
          <td>{row['issues']}</td>
          <td style="font-size:12px;color:#555">{row['details']}</td>
          <td style="font-size:11px;color:#888">{row['source_file']}</td>
          <td><span style="background:{color};color:white;padding:3px 10px;
              border-radius:12px;font-weight:bold">{row['risk_score']}</span></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Invoice Risk Scanner - Exception Dashboard</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 32px; background:#fafafa; }}
  h1 {{ color:#1a1a2e; }}
  .summary {{ display:flex; gap:16px; margin-bottom:24px; }}
  .card {{ background:white; border-radius:10px; padding:16px 24px; box-shadow:0 1px 4px rgba(0,0,0,0.1); }}
  .card .num {{ font-size:28px; font-weight:bold; }}
  table {{ width:100%; border-collapse:collapse; background:white; border-radius:10px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,0.1); }}
  th, td {{ padding:10px 12px; text-align:left; border-bottom:1px solid #eee; vertical-align:top; }}
  th {{ background:#1a1a2e; color:white; font-size:13px; text-transform:uppercase; }}
  tr:hover {{ background:#f5f5f5; }}
</style>
</head>
<body>
  <h1>Invoice Risk Scanner — Exception Dashboard</h1>
  <div class="summary">
    <div class="card"><div class="num">{len(exceptions_df)}</div>Flagged invoices</div>
    <div class="card"><div class="num">{(exceptions_df['risk_score'] >= 60).sum()}</div>High risk</div>
    <div class="card"><div class="num">{exceptions_df['risk_score'].mean():.0f}</div>Avg risk score</div>
  </div>
  <table>
    <tr>
      <th>Invoice #</th><th>Vendor</th><th>GSTIN</th><th>Amount</th>
      <th>Issues</th><th>Details</th><th>Source file</th><th>Risk score</th>
    </tr>
    {rows_html}
  </table>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")


def demo_data():
    """Synthetic invoices matching sample_data/sample_ledger.csv, for a
    dependency-free demo run (no OCR libs / API key required)."""
    return [
        {"source_file": "demo/INV-101.pdf", "invoice_number": "INV-101",
         "vendor_name": "Vicky Pvt Ltd", "gstin": "29AFSPB9500E1ZY",
         "date": "18/06/2026", "total_amount": 11800.0},
        {"source_file": "demo/INV-101-copy.pdf", "invoice_number": "INV-101",
         "vendor_name": "Vicky Pvt Ltd", "gstin": "29AFSPB9500E1ZY",
         "date": "18/06/2026", "total_amount": 11800.0},  # duplicate
        {"source_file": "demo/INV-102.pdf", "invoice_number": "INV-102",
         "vendor_name": "Acme Traders", "gstin": "27AAACA1234A1Z5",
         "date": "20/06/2026", "total_amount": 6200.0},  # amount mismatch (ledger: 5900)
        {"source_file": "demo/INV-105.pdf", "invoice_number": "INV-105",
         "vendor_name": "Unknown Supplies Co", "gstin": "07XYZAB1234C1Z9",
         "date": "27/06/2026", "total_amount": 3000.0},  # missing from ledger + not in vendor master
        {"source_file": "demo/INV-103.pdf", "invoice_number": "INV-103",
         "vendor_name": "Sunrise Enterprises", "gstin": "BAD-GSTIN",
         "date": "22/06/2026", "total_amount": 17700.0},  # invalid GSTIN format
    ]


def main():
    parser = argparse.ArgumentParser(description="AI-powered invoice risk scanner")
    parser.add_argument("--invoices", help="Folder of invoice PDFs/images")
    parser.add_argument("--ledger", help="Purchase ledger CSV path")
    parser.add_argument("--vendor-master", help="Vendor master CSV path (optional)")
    parser.add_argument("--api-key", default=os.environ.get("SANDBOX_API_KEY"))
    parser.add_argument("--api-secret", default=os.environ.get("SANDBOX_API_SECRET"))
    parser.add_argument("--demo", action="store_true",
                         help="Run with bundled synthetic data, no files/API key needed")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.demo:
        invoices = demo_data()
        ledger_df = pd.read_csv("sample_data/sample_ledger.csv")
        vendor_master_df = pd.read_csv("sample_data/sample_vendor_master.csv")
    else:
        if not args.invoices or not args.ledger:
            parser.error("--invoices and --ledger are required unless --demo is set")
        invoices = run_extraction(args.invoices)
        ledger_df = pd.read_csv(args.ledger)
        vendor_master_df = pd.read_csv(args.vendor_master) if args.vendor_master else None

    gstin_lookup = run_gstin_verification(invoices, args.api_key, args.api_secret)

    exceptions_df = reconcile(invoices, ledger_df, vendor_master_df, gstin_lookup)

    if exceptions_df.empty:
        print("No exceptions found - all invoices reconciled cleanly.")
        return

    csv_path = os.path.join(OUTPUT_DIR, "exceptions.csv")
    html_path = os.path.join(OUTPUT_DIR, "dashboard.html")
    exceptions_df.to_csv(csv_path, index=False)
    build_dashboard_html(exceptions_df, html_path)

    print(f"{len(exceptions_df)} exception(s) found.")
    print(f"  -> {csv_path}")
    print(f"  -> {html_path}")


if __name__ == "__main__":
    main()
