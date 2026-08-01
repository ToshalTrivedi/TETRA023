"""
GSTIN Validation Utilities
---------------------------
GSTIN format: 15 characters
[2-digit state code][10-char PAN][1 entity code][Z][1 checksum]
e.g. 24AAACS1234F1Z5

This module checks:
1. Format validity (regex)
2. State code plausibility (first 2 digits map to a real Indian state code)
3. State-code cross-validation against the vendor master's registered state
   (a mismatch can indicate a cloned/incorrect GSTIN used on a fake invoice)
"""

import re

GSTIN_REGEX = re.compile(
    r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
)

# Official GST state codes (subset covering common states; extend as needed)
STATE_CODES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi",
    "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
    "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
    "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh",
    "23": "Madhya Pradesh", "24": "Gujarat", "26": "Dadra and Nagar Haveli",
    "27": "Maharashtra", "28": "Andhra Pradesh (Old)", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman and Nicobar", "36": "Telangana",
    "37": "Andhra Pradesh",
}


def is_valid_format(gstin: str) -> bool:
    if not gstin or not isinstance(gstin, str):
        return False
    return bool(GSTIN_REGEX.match(gstin.strip().upper()))


def get_state_from_gstin(gstin: str) -> str | None:
    if not gstin or len(gstin) < 2:
        return None
    return STATE_CODES.get(gstin[:2])


def check_state_match(gstin: str, expected_state: str) -> bool:
    """Returns True if GSTIN's embedded state matches the vendor master's registered state."""
    gstin_state = get_state_from_gstin(gstin)
    if gstin_state is None or not expected_state:
        return False
    return gstin_state.strip().lower() == expected_state.strip().lower()


def validate_gstin_full(gstin: str, expected_state: str = None) -> dict:
    """Full validation report for a single GSTIN."""
    result = {
        "gstin": gstin,
        "format_valid": is_valid_format(gstin),
        "state_from_gstin": get_state_from_gstin(gstin),
        "state_match": None,
    }
    if expected_state:
        result["state_match"] = check_state_match(gstin, expected_state)
    return result


if __name__ == "__main__":
    tests = [
        ("24AAACS1234F1Z5", "Gujarat"),   # valid, matches
        ("27AAACS1234F1Z5", "Gujarat"),   # valid format, state mismatch
        ("29AAZZZ0000A1Z1", None),        # unknown vendor
        ("INVALIDGSTIN", "Delhi"),        # bad format
    ]
    for gstin, state in tests:
        print(validate_gstin_full(gstin, state))


