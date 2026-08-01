# Invoice Risk Screening Module
**Indo-French AI Innovation Sprint — Invoice Audit & Reconciliation Prototype**

## Problem
Manual invoice vouching is slow and sample-based, so duplicate invoices,
incorrect GST details, unsupported transactions, and ledger mismatches can
go undetected. This prototype automates the screening of **100% of invoices**
instead of a manual sample, and prioritizes human attention on the riskiest ones.

## Architecture

```
Invoice PDF/Image
      │
      ▼
Extraction Engine (extraction/extract.py)
  - Vision LLM (Claude) reads invoice, outputs structured JSON
  - Per-field confidence score
      │
      ▼
Reconciliation Engine (reconciliation/engine.py)
  - Matches invoice_number against Purchase Ledger
  - Cross-checks GSTIN format + state code against Vendor Master
  - Exact duplicate detection
  - Near-duplicate detection (fuzzy match on invoice number, same
    vendor+amount+date)
  - Vendor activity baselining (flags invoices >150% of vendor's average)
      │
      ▼
Risk Scoring
  - Weighted rule-based score (0-100), NOT a black-box ML score
  - Every flag comes with a plain-English explanation of why
      │
      ▼
Dashboard (dashboard/app.py — Streamlit)
  - Prioritized exception table, filterable by risk/type/search
  - Per-invoice audit trail: extracted data + ledger match + exceptions
```

## Why this design (talking points for mentors)

- **Vision LLM over custom OCR model**: no labeled training data available in
  hackathon timeframe; vision LLMs handle varied invoice layouts out of the box.
- **Rule-based scoring over ML classifier**: audit use cases require
  explainability — "why was this flagged" matters more than raw accuracy for
  trust and adoption. Also works well on small/synthetic datasets where an ML
  model would overfit or need more data than we have.
- **Fuzzy matching (rapidfuzz) for near-duplicates**: catches invoices that
  are duplicated with a slightly altered invoice number — a common evasion
  pattern that pure exact-match tools miss.
- **GSTIN state cross-validation**: extracts the embedded state code from the
  GSTIN and compares it against the vendor's registered state — a
  India-specific compliance check most generic invoice tools skip.
- **Auto-clear + workload reduction metric**: reframes the tool from "finds
  problems" to "tells you which 90% you can skip reviewing," which is the
  actual business value auditors care about.

## Setup

```bash
pip install -r requirements.txt
cd dashboard
streamlit run app.py
```

The dashboard defaults to bundled sample data (`data/`) so it runs with zero
config for demo purposes. Sample data includes deliberately planted
anomalies: an exact duplicate, a near-duplicate, a GSTIN mismatch, a missing
ledger record, an amount mismatch, and an unusual vendor spike — all of which
the engine correctly detects.

To run extraction on real invoice files:
```bash
export ANTHROPIC_API_KEY=your_key
export INVOICE_FOLDER=path/to/invoices
python extraction/extract.py
```

## What's built vs. what's next

**Built:**
- End-to-end pipeline: extraction → reconciliation → risk scoring → dashboard
- 6 detection rules with explainable scoring
- Searchable audit trail linking every exception to source document

**Next (production path):**
- Replace CSV ledger/vendor inputs with direct ERP/Tally/SAP integration
- Persist results in a proper DB (Postgres) instead of in-memory pandas
- Human feedback loop: mark false positives to auto-tune rule weights
- OCR confidence routing: auto-route low-confidence extractions to manual review queue
