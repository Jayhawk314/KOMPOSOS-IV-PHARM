# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Client identification for NCBI E-utilities requests.

Why this exists
---------------
NCBI asks every E-utilities client to identify itself with `tool` and `email`,
and rate-limits anonymous callers to 3 requests/second. The documented remedy
for an abusive client is blocking its IP address.

For a repository run by a few people that is merely untidy. For a shared public
deployment it is an operational risk: every user's searches arrive from one
server address, so a single block takes the feature down for everyone.

Set `NCBI_API_KEY` and `NCBI_CONTACT_EMAIL` in the environment. An API key
raises the ceiling to 10 requests/second. Nothing is committed here.

Kept as its own module so both callers can share it without dragging in the
graph-loading import chain.
"""
from __future__ import annotations

import os

NCBI_TOOL = "KOMPOSOS-IV-PHARM"
DEFAULT_CONTACT_EMAIL = "jhawk314@gmail.com"


def contact_email() -> str:
    return os.environ.get("NCBI_CONTACT_EMAIL", DEFAULT_CONTACT_EMAIL)


def api_key() -> str:
    return os.environ.get("NCBI_API_KEY", "").strip()


def ncbi_credentials() -> dict[str, str]:
    """Client-identification parameters to add to every E-utilities request."""
    parameters = {"tool": NCBI_TOOL, "email": contact_email()}
    key = api_key()
    if key:
        parameters["api_key"] = key
    return parameters


def ncbi_min_interval() -> float:
    """Seconds between requests: 3/s anonymous, 10/s with an API key."""
    return 0.11 if api_key() else 0.34
