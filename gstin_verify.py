"""
gstin_verify.py
----------------
Thin wrapper around Sandbox's (sandbox.co.in) GST Compliance API for
validating a GSTIN format-wise and, optionally, against the live
GSTN/IRP record (status, legal name, etc).

Get your API key + secret from https://developer.sandbox.co.in

Usage:
    from gstin_verify import is_valid_gstin_format, SandboxGSTINClient

    client = SandboxGSTINClient(api_key="...", api_secret="...")
    result = client.search_gstin("29AFSPB9500E1ZY")
"""

import re
import time
import requests

GSTIN_REGEX = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

BASE_URL = "https://api.sandbox.co.in"


def is_valid_gstin_format(gstin):
    """Cheap local check - no API call needed. Filters out obvious junk
    (bad OCR reads, missing fields) before you spend an API call."""
    if not gstin:
        return False
    return bool(GSTIN_REGEX.match(gstin.strip().upper()))


class SandboxGSTINClient:
    def __init__(self, api_key, api_secret, api_version="1.0"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_version = api_version
        self._token = None
        self._token_expiry = 0

    def _authenticate(self):
        url = f"{BASE_URL}/authenticate"
        headers = {
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret,
            "x-api-version": self.api_version,
        }
        resp = requests.post(url, headers=headers, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        self._token = payload["access_token"]
        # Give ourselves a minute of buffer before actual expiry.
        self._token_expiry = time.time() + payload.get("expires_in", 3300) - 60
        return self._token

    def _get_token(self):
        if self._token is None or time.time() >= self._token_expiry:
            self._authenticate()
        return self._token

    def search_gstin(self, gstin):
        """Look up a GSTIN. Returns a normalized dict:
        {ok, status, legal_name, trade_name, registration_date, raw}
        Returns ok=False with an 'error' key if the lookup fails
        (invalid GSTIN, not found, API error, etc) rather than raising,
        so the reconciliation pipeline can keep processing other invoices.
        """
        if not is_valid_gstin_format(gstin):
            return {"ok": False, "error": "invalid_format", "gstin": gstin}

        token = self._get_token()
        url = f"{BASE_URL}/gst/compliance/public/gstin/search"
        headers = {
            "Content-Type": "application/json",
            "authorization": token,
            "x-api-key": self.api_key,
        }
        try:
            resp = requests.post(url, headers=headers, json={"gstin": gstin}, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
            data = payload.get("data", {}).get("data", {})
            if not data:
                return {"ok": False, "error": "not_found", "gstin": gstin}
            return {
                "ok": True,
                "gstin": data.get("gstin", gstin),
                "status": data.get("sts"),
                "legal_name": data.get("lgnm"),
                "trade_name": data.get("tradeNam"),
                "registration_date": data.get("rgdt"),
                "taxpayer_type": data.get("dty"),
                "raw": data,
            }
        except requests.RequestException as exc:
            return {"ok": False, "error": str(exc), "gstin": gstin}


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 4:
        print("Usage: python gstin_verify.py <api_key> <api_secret> <gstin>")
        sys.exit(1)

    client = SandboxGSTINClient(api_key=sys.argv[1], api_secret=sys.argv[2])
    print(json.dumps(client.search_gstin(sys.argv[3]), indent=2, default=str))
