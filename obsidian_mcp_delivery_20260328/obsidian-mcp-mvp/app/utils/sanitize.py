from __future__ import annotations

import re


def clean_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def clean_tag(tag: str) -> str:
    return re.sub(r"\s+", "-", tag.strip().lower())
