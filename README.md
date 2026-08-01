# AI-Powered Invoice Risk Scanner — Prototype

A minimal, working prototype for **Track C: FinTech — Problem Statement 1**.
Reads invoices (PDF/image), extracts key fields, verifies GSTINs, reconciles
against a purchase ledger, and outputs a prioritized, risk-scored exception
dashboard with a full audit trail.

## How it maps to the brief

| Expected outcome | Where it lives |
|---|---|
| Data Extraction Engine | `extract_invoice.py` — pdfplumber text extraction with OCR (pytesseract) fallback for scanned invoices; regex parsing for invoice number, date, vendor, GSTIN, taxable value, tax, total |
| Reconciliation & Anomaly Detection | `reconcile.py` — duplicate invoices, missing ledger records, amount/date mismatches, invalid GSTIN format, unusual/unknown vendors |
| Audit Trail & Risk Scoring | Every exception row keeps `source_file` (link to original doc) + a 0-100 `risk_score` |
| Dashboarding | `main.py` → `output/dashboard.html` (searchable-by-eye HTML table, sortable by risk) + `output/exceptions.csv` |

## Quick start (no setup needed)

```bash
pip install -r requirements.txt
python main.py --demo
```

This runs the whole pipeline on bundled synthetic data (`sample_data/`) and
writes `output/exceptions.csv` + `output/dashboard.html`. Open the HTML file
in a browser to see the dashboard.

## Running on real invoices

```bash
python main.py \
  --invoices ./my_invoices_folder \
  --ledger ./purchase_ledger.csv \
  --vendor-master ./vendor_master.csv \
  --api-key YOUR_SANDBOX_API_KEY \
  --api-secret YOUR_SANDBOX_API_SECRET
```

- `--invoices`: folder of `.pdf` / `.jpg` / `.png` invoice files
- `--ledger`: CSV with columns `invoice_number, vendor_name, gstin, date, taxable_value, tax_amount, total_amount`
- `--vendor-master`: optional CSV with a `gstin` column of approved vendors
- `--api-key` / `--api-secret`: from [developer.sandbox.co.in](https://developer.sandbox.co.in) — used to verify GSTIN status/legal name live against the GST Network. Omit to skip live verification and fall back to local format-only checks.

## OCR system dependencies

For scanned PDFs/images you need Tesseract + Poppler installed on the machine
(these are OS packages, not pip packages):

```bash
# Debian/Ubuntu
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler
```

## File-by-file

- `extract_invoice.py` — field extraction (text + OCR)
- `gstin_verify.py` — Sandbox GSTIN search API wrapper + local format validator
- `reconcile.py` — matching, anomaly detection, risk scoring
- `main.py` — CLI orchestrator, wires everything together, builds the dashboard
- `sample_data/` — synthetic ledger + vendor master for testing/demo

## Known limitations (it's a hackathon prototype, not production)

- Vendor-name extraction is heuristic (first line / "From:" pattern) — real
  invoices vary a lot in layout, so expect misses on unusual templates.
  A next step would be a small layout-aware model (e.g. LayoutLM) or an
  LLM-based extractor instead of pure regex.
- Amount/date matching assumes the ledger uses the same date format as what
  gets extracted (`dd/mm/yyyy`) — add date normalization for production use.
- Risk weights in `reconcile.py` are illustrative; tune them with your audit
  team's actual risk appetite.
