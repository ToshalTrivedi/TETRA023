"""
extract_invoice.py
-------------------
Reads an invoice (PDF or image) and pulls out the key fields the
hackathon brief asks for: invoice number, date, vendor name, GSTIN,
taxable value, tax amount, total amount.

Strategy:
1. If it's a PDF, try text extraction first (pdfplumber) - works for
   digitally-generated invoices.
2. If the PDF has little/no extractable text (i.e. it's a scanned
   image) or the input is a JPG/PNG, fall back to OCR (pytesseract).
3. Run a set of regex patterns over the extracted text to pull each
   field. Multiple pattern variants are tried per field since invoice
   layouts vary a lot.

This is a *prototype* extraction engine, not a production parser.
For garbled OCR text, fields will come back as None - the
reconciliation layer treats a missing field as a risk signal.
"""

import re
from pathlib import Path

import pdfplumber
from PIL import Image
import pytesseract

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


GSTIN_REGEX = r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b"

# Matches the gap between a label ("Taxable Value", "Invoice Total"...) and
# the actual number, tolerating: a rate annotation in parentheses e.g.
# "(9%)", a colon/dash, and 0-4 stray non-digit characters (garbled
# currency symbols - OCR often reads ₹ as %, Rs, or junk). Requires two
# decimal places so it doesn't grab a bare quantity like "80".
AMOUNT_GAP = r"\s*(?:\([^)]{0,10}\))?\s*[:\-]?\s*[^\d\n]{0,4}([\d,]+\.\d{2})"

FIELD_PATTERNS = {
    "invoice_number": [
        r"invoice\s*(?:no|number|#)\.?\s*[:\-]?\s*([A-Za-z0-9\/\-]+)",
        r"inv\s*(?:no|#)\.?\s*[:\-]?\s*([A-Za-z0-9\/\-]+)",
        r"bill\s*(?:no|number)\.?\s*[:\-]?\s*([A-Za-z0-9\/\-]+)",
    ],
    "date": [
        r"invoice\s*date\s*[:\-]?\s*([0-3]?\d[\/\-.][01]?\d[\/\-.]\d{2,4})",
        r"\bdate\s*[:\-]?\s*([0-3]?\d[\/\-.][01]?\d[\/\-.]\d{2,4})",
    ],
    "taxable_value": [
        r"taxable\s*value" + AMOUNT_GAP,
        r"taxable\s*amount" + AMOUNT_GAP,
    ],
    "tax_amount": [
        r"(?:total\s*)?tax\s*amount" + AMOUNT_GAP,
    ],
    # CGST/SGST/IGST are matched separately and summed in _extract_tax_amount,
    # since most invoices list them as separate line items, not one field.
    "cgst": [r"(?:total\s*)?cgst" + AMOUNT_GAP],
    "sgst": [r"(?:total\s*)?sgst" + AMOUNT_GAP],
    "igst": [r"(?:total\s*)?igst" + AMOUNT_GAP],
    "total_amount": [
        r"invoice\s*total" + AMOUNT_GAP,
        r"grand\s*total" + AMOUNT_GAP,
        r"total\s*amount" + AMOUNT_GAP,
        r"\btotal\b" + AMOUNT_GAP,
    ],
}

VENDOR_LINE_HINTS = [
    r"(?:from|seller|vendor|supplier)\s*[:\-]\s*(.+)",
]

COMPANY_SUFFIXES = ("pvt", "ltd", "llp", "enterprises", "traders",
                     "industries", "company", "corp", "inc", "co.")


def _clean_number(raw):
    if raw is None:
        return None
    try:
        return float(raw.replace(",", "").strip())
    except ValueError:
        return None


def _extract_text_from_pdf(path):
    """Try native text extraction; return '' if the PDF is basically empty
    of text (i.e. it's a scan and needs OCR)."""
    text_chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
    text = "\n".join(text_chunks)
    return text


def _ocr_pdf(path):
    if not PDF2IMAGE_AVAILABLE:
        raise RuntimeError(
            "pdf2image (and poppler) not installed - can't OCR scanned PDFs. "
            "Install poppler-utils and `pip install pdf2image`."
        )
    images = convert_from_path(path)
    text = "\n".join(pytesseract.image_to_string(img) for img in images)
    return text


def _ocr_image(path):
    img = Image.open(path)
    return pytesseract.image_to_string(img)


def get_text(file_path):
    """Return raw extracted text for a PDF or image invoice."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        text = _extract_text_from_pdf(path)
        # Heuristic: if there's barely any text, it's a scanned PDF -> OCR it
        if len(text.strip()) < 30:
            text = _ocr_pdf(path)
        return text

    if suffix in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        return _ocr_image(path)

    raise ValueError(f"Unsupported file type: {suffix}")


def _find_first_match(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _guess_vendor_name(text):
    for pattern in VENDOR_LINE_HINTS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().splitlines()[0]

    # Scope the search to the text before the seller's own GSTIN mention
    # (or "Bill To", whichever comes first) - that's almost always the
    # seller's letterhead/address block, and it excludes the buyer's name
    # which appears further down under "Bill To".
    gstin_match = re.search(GSTIN_REGEX, text)
    bill_to_match = re.search(r"bill\s*to", text, flags=re.IGNORECASE)
    cutoffs = [m.start() for m in (gstin_match, bill_to_match) if m]
    scoped_text = text[: min(cutoffs)] if cutoffs else text[:800]

    # Prefer the line closest to the GSTIN/Bill-To marker that contains a
    # company-name suffix and has more than one word (filters out stray
    # single-word OCR fragments like a logo icon misread as "Enterprises").
    candidate = None
    for line in scoped_text.splitlines():
        line = line.strip()
        if not line:
            continue
        low = line.lower()
        if len(line.split()) >= 2 and any(suf in low for suf in COMPANY_SUFFIXES):
            candidate = line  # last match wins - closest to the GSTIN line
    if candidate:
        return candidate

    # Fallback: first substantial line of the document.
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 3:
            return line
    return None


def _extract_tax_amount(text):
    """Prefer an explicit combined 'tax amount' label. If the invoice
    instead lists CGST/SGST (or IGST) separately - the common case for
    Indian tax invoices - sum those instead."""
    direct = _clean_number(_find_first_match(FIELD_PATTERNS["tax_amount"], text))
    if direct is not None:
        return direct

    cgst = _clean_number(_find_first_match(FIELD_PATTERNS["cgst"], text))
    sgst = _clean_number(_find_first_match(FIELD_PATTERNS["sgst"], text))
    if cgst is not None and sgst is not None:
        return round(cgst + sgst, 2)

    igst = _clean_number(_find_first_match(FIELD_PATTERNS["igst"], text))
    if igst is not None:
        return igst

    return None


def extract_invoice_fields(file_path):
    """Main entry point. Returns a dict of extracted fields plus the
    raw text (kept for debugging / audit trail)."""
    text = get_text(file_path)

    gstin_matches = re.findall(GSTIN_REGEX, text)

    fields = {
        "source_file": str(file_path),
        "invoice_number": _find_first_match(FIELD_PATTERNS["invoice_number"], text),
        "date": _find_first_match(FIELD_PATTERNS["date"], text),
        "vendor_name": _guess_vendor_name(text),
        # First GSTIN found is assumed to be the vendor/supplier GSTIN.
        # If two are found, the second is often the buyer's GSTIN.
        "gstin": gstin_matches[0] if gstin_matches else None,
        "all_gstins_found": gstin_matches,
        "taxable_value": _clean_number(_find_first_match(FIELD_PATTERNS["taxable_value"], text)),
        "tax_amount": _extract_tax_amount(text),
        "total_amount": _clean_number(_find_first_match(FIELD_PATTERNS["total_amount"], text)),
        "raw_text": text,
    }
    return fields


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python extract_invoice.py <invoice_file>")
        sys.exit(1)

    result = extract_invoice_fields(sys.argv[1])
    result.pop("raw_text")  # keep console output readable
    print(json.dumps(result, indent=2, default=str))
