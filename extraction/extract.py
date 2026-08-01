"""
Invoice Extraction Engine — FREE / LOCAL VERSION
----------------------------------------------------
No API calls, no cost. Uses pdfplumber to read text directly from PDFs,
and Tesseract OCR to read text from images (jpg/png). Regex pattern
matching pulls out invoice fields from the extracted text.

Requires (one-time setup):
  pip install pdfplumber pytesseract pillow
  Install Tesseract OCR (Windows): https://github.com/UB-Mannheim/tesseract/wiki
  Default install path assumed: C:\\Program Files\\Tesseract-OCR\\tesseract.exe
  (If yours installed elsewhere, update TESSERACT_PATH below.)
"""

import re
from pathlib import Path

import pdfplumber

# Update this path if Tesseract installed somewhere else on your machine
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_pdf(file_path: str) -> str:
    """Pulls all text out of a PDF using pdfplumber (free, local, no API)."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_image(file_path: str) -> str:
    """OCR for image invoices (jpg/png) using Tesseract."""
    try:
        import pytesseract
        from PIL import Image

        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"OCR failed ({e}). Make sure Tesseract OCR is installed at: {TESSERACT_PATH}")
        return ""


def parse_invoice_fields(text: str) -> dict:
    """
    Regex-based field extraction from raw invoice text.
    Patterns are broad to catch common invoice formats.
    """

    def find(pattern, default=None):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    invoice_number = find(r"invoice\s*(?:no\.?|number|#)\s*[:\-]?\s*([A-Z0-9\-\/]+)")
    invoice_date = find(r"(?:invoice\s*date|date)\s*[:\-]?\s*([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4}|\d{4}-\d{2}-\d{2})")
    gstin = find(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b")
    vendor_name = find(r"(?:vendor|supplier|from|seller|bill\s*from)\s*(?:name)?\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)")

    taxable_value = find(r"(?:taxable\s*value|sub\s*total|subtotal)\s*[:\-]?\s*(?:₹|rs\.?)?\s*([\d,]+\.?\d*)")
    tax_amount = find(r"(?:tax\s*amount|gst|cgst\s*\+\s*sgst|igst)\s*[:\-]?\s*(?:₹|rs\.?)?\s*([\d,]+\.?\d*)")
    total_amount = find(r"(?:total\s*amount|grand\s*total|total)\s*[:\-]?\s*(?:₹|rs\.?)?\s*([\d,]+\.?\d*)")

    def clean_number(val):
        if val is None:
            return None
        return float(val.replace(",", ""))

    return {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "vendor_name": vendor_name,
        "gstin": gstin,
        "taxable_value": clean_number(taxable_value),
        "tax_amount": clean_number(tax_amount),
        "total_amount": clean_number(total_amount),
    }


def extract_invoice(file_path: str) -> dict:
    """
    Main entry point. Reads a PDF or image invoice and returns extracted
    fields as a dict. No API key, no cost, fully local.
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
        if not raw_text.strip():
            return {"error": "PDF has no extractable text (likely a scanned image PDF)"}
    elif ext in (".jpg", ".jpeg", ".png"):
        raw_text = extract_text_from_image(file_path)
    else:
        return {"error": f"Unsupported file type: {ext}"}

    if not raw_text.strip():
        return {"error": "Could not extract any text from file"}

    fields = parse_invoice_fields(raw_text)
    fields["_raw_text_preview"] = raw_text[:500]
    return fields


if __name__ == "__main__":
    raw_input_path = input("Enter path to a PDF/image invoice to test: ").strip()
    test_file = raw_input_path.strip('"').strip("'")

    result = extract_invoice(test_file)
    import json
    print(json.dumps(result, indent=2))

    