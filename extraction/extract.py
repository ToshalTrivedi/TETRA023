"""
Invoice Extraction Engine
--------------------------
Uses a vision-capable LLM (Claude) to read invoice PDFs/images and pull out
structured fields. Falls back gracefully and returns a confidence score per
field so low-confidence extractions can be routed to manual review.

For the hackathon demo, extracted_invoices.csv simulates the OUTPUT of this
module so the reconciliation/dashboard can be demoed without needing live
API calls during judging (avoids demo failure risk from network/API issues).
To actually run extraction on real files, set ANTHROPIC_API_KEY and call
extract_invoice() below.
"""

import base64
import json
import os
from pathlib import Path

import anthropic

EXTRACTION_PROMPT = """You are an invoice data extraction engine for an audit tool.
Read the attached invoice image/PDF and extract the following fields.
Return ONLY valid JSON, no preamble, no markdown fences.

Fields to extract:
- invoice_number (string)
- invoice_date (YYYY-MM-DD)
- vendor_name (string)
- gstin (string, 15-character Indian GST number if present)
- taxable_value (number, pre-tax amount)
- tax_amount (number, total GST/CGST+SGST/IGST)
- total_amount (number, final payable amount)

For each field also give a confidence score from 0-1 based on how clearly
it was visible/legible in the document.

Return JSON in this exact shape:
{
  "invoice_number": {"value": "...", "confidence": 0.95},
  "invoice_date": {"value": "...", "confidence": 0.95},
  "vendor_name": {"value": "...", "confidence": 0.95},
  "gstin": {"value": "...", "confidence": 0.95},
  "taxable_value": {"value": 0, "confidence": 0.95},
  "tax_amount": {"value": 0, "confidence": 0.95},
  "total_amount": {"value": 0, "confidence": 0.95}
}

If a field is missing or illegible, set value to null and confidence to 0.
"""


def extract_invoice(file_path: str, model: str = "claude-sonnet-4-6") -> dict:
    """
    Extract structured fields from a single invoice file (PDF or image).
    Returns a dict of field -> {value, confidence}.
    """
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    file_bytes = Path(file_path).read_bytes()
    b64_data = base64.standard_b64encode(file_bytes).decode("utf-8")
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        content_block = {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": b64_data},
        }
    else:
        media_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        content_block = {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": b64_data},
        }

    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [content_block, {"type": "text", "text": EXTRACTION_PROMPT}],
            }
        ],
    )

    raw_text = "".join(block.text for block in response.content if block.type == "text")
    cleaned = raw_text.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Extraction failed to parse -> flag entire doc for manual review
        return {"error": "extraction_parse_failed", "raw": raw_text}


def extract_batch(folder_path: str) -> list[dict]:
    """Run extraction on every PDF/image in a folder. Returns list of results."""
    results = []
    for file_path in Path(folder_path).glob("*"):
        if file_path.suffix.lower() in (".pdf", ".jpg", ".jpeg", ".png"):
            result = extract_invoice(str(file_path))
            result["source_file"] = file_path.name
            results.append(result)
    return results


if __name__ == "__main__":
    # Demo: point this at a folder of real invoice files when you have them
    folder = os.environ.get("INVOICE_FOLDER", "../data/sample_invoices")
    if Path(folder).exists():
        out = extract_batch(folder)
        print(json.dumps(out, indent=2))
    else:
        print(f"No folder at {folder} — using pre-extracted data/extracted_invoices.csv for demo instead.")
