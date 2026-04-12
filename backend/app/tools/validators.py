"""Validation utilities — HTML structure checks, key element presence, hallucination detection."""

import re
from typing import Optional

from bs4 import BeautifulSoup

from app.models.ad_context import AdContext
from app.models.qa_report import HallucinationFlag, StructuralIssue
from app.models.semantic_map import SemanticMap


def validate_html_structure(modified_html: str) -> list[StructuralIssue]:
    """
    Parse modified HTML and check for critical structural problems.
    Returns a list of StructuralIssue — empty if no issues found.
    """
    issues: list[StructuralIssue] = []

    try:
        soup = BeautifulSoup(modified_html, "lxml")
    except Exception as e:
        issues.append(StructuralIssue(
            severity="critical",
            code="HTML_PARSE_ERROR",
            message=f"HTML could not be parsed: {e}",
        ))
        return issues

    # Check body exists and has content
    body = soup.find("body")
    if not body or len(body.get_text(strip=True)) < 50:
        issues.append(StructuralIssue(
            severity="critical",
            code="EMPTY_BODY",
            message="Modified HTML body appears empty or has very little content",
        ))

    # Check for broken script tags that might have been damaged
    for script in soup.find_all("script"):
        content = script.string or ""
        # Look for obviously truncated JS (open brackets without close)
        if content.count("{") > content.count("}") + 5:
            issues.append(StructuralIssue(
                severity="warning",
                code="POSSIBLE_SCRIPT_CORRUPTION",
                message="A <script> block may have been truncated or corrupted",
                selector="script",
            ))
            break

    return issues


def check_key_elements(modified_html: str, semantic_map: SemanticMap) -> bool:
    """
    Verify that key elements from the original SemanticMap are still present
    in the modified HTML. Returns True if all critical elements are present.
    """
    soup = BeautifulSoup(modified_html, "lxml")

    critical_selectors = []

    if semantic_map.hero_headline:
        critical_selectors.append(semantic_map.hero_headline.selector)
    if semantic_map.primary_cta:
        critical_selectors.append(semantic_map.primary_cta.selector)

    for selector in critical_selectors:
        try:
            if not soup.select(selector):
                return False
        except Exception:
            # Invalid selector — treat as missing
            return False

    return True


def detect_hallucinations(
    original_html: str,
    modified_html: str,
    ad_context: AdContext,
) -> list[HallucinationFlag]:
    """
    Check if the modified HTML introduces any content not grounded in
    the original page or the ad creative.

    Currently checks for:
    - New discount percentages not matching the ad
    - Discount codes not present in the ad
    """
    flags: list[HallucinationFlag] = []

    original_text = BeautifulSoup(original_html, "lxml").get_text(" ", strip=True)
    modified_text = BeautifulSoup(modified_html, "lxml").get_text(" ", strip=True)

    # ── Check for new discount percentages ────────────────────────────────────
    percent_pattern = re.compile(r"(\d+)\s*%\s*(?:off|OFF|discount)", re.I)

    original_percents = {int(m.group(1)) for m in percent_pattern.finditer(original_text)}
    modified_percents = {int(m.group(1)) for m in percent_pattern.finditer(modified_text)}
    ad_percent = int(ad_context.discount_percent) if ad_context.discount_percent else None

    new_percents = modified_percents - original_percents
    for pct in new_percents:
        # Only flag if it doesn't match the ad's discount
        if ad_percent is None or abs(pct - ad_percent) > 2:
            flags.append(HallucinationFlag(
                code="NEW_DISCOUNT_VALUE",
                message=f"Modified page introduces '{pct}% OFF' not found in original or ad",
                offending_text=f"{pct}% OFF",
            ))

    # ── Check for invented promo codes ────────────────────────────────────────
    code_pattern = re.compile(r"\b([A-Z]{3,10}\d*)\b")
    original_codes = set(code_pattern.findall(original_text))
    modified_codes = set(code_pattern.findall(modified_text))
    ad_code = ad_context.discount_code or ""

    new_codes = modified_codes - original_codes
    for code in new_codes:
        if code != ad_code and len(code) >= 4:
            # Heuristic: looks like a promo code
            flags.append(HallucinationFlag(
                code="INVENTED_PROMO_CODE",
                message=f"Promo code '{code}' appears in modified page but not in original or ad",
                offending_text=code,
            ))

    return flags
