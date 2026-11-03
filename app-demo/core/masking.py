"""Personal-data masking (Colombian Law 1581 of 2012).

The ID number (cédula) comes in through the keypad and is never stored in full:
only the last 3 digits are kept.
"""

from __future__ import annotations

import re

_NON_DIGITS = re.compile(r"\D")
_ID_NUMBER = re.compile(r"^\d{6,10}$")  # Colombian citizen ID: 6 to 10 digits


def normalize_id_number(dtmf: str) -> str | None:
    """Return only the digits if it looks like a valid ID number; otherwise None.

    The operator ends with '#', which is dropped along with any other symbol.
    """
    digits = _NON_DIGITS.sub("", dtmf or "")
    return digits if _ID_NUMBER.match(digits) else None


# 6+ digits, optionally separated by spaces, dots or dashes ("10 123 456", "10.123.456").
_DIGIT_RUN = re.compile(r"\d(?:[\s.\-]?\d){5,}")


def mask_numbers_in_text(text: str) -> str:
    """Mask any spoken/typed run of 6+ digits in free text (e.g. a transcript turn).

    The operator might say their ID number out loud even though the agent asks for the keypad.
    """
    return _DIGIT_RUN.sub(lambda m: mask_id_number(m.group(0)), text or "")


def mask_id_number(id_number: str) -> str:
    digits = _NON_DIGITS.sub("", id_number or "")
    if len(digits) <= 3:
        return "*" * len(digits)
    return "*" * (len(digits) - 3) + digits[-3:]
