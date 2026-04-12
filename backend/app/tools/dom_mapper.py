"""Semantic DOM mapping — identifies hero, CTAs, and social proof elements in raw HTML."""

import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

from app.models.semantic_map import PageElement, SemanticMap
from app.tools.shopify import get_shopify_hero_selectors


# ── Public API ────────────────────────────────────────────────────────────────

def map_semantic_elements(raw_html: str, is_shopify: bool = False) -> dict:
    """
    Parse HTML and identify semantic elements using DOM heuristics.
    Returns a dict of role strings to PageElement objects.
    """
    soup = BeautifulSoup(raw_html, "lxml")
    elements: dict = {}

    _find_hero(soup, elements, is_shopify)
    _find_announcement_bar(soup, elements)
    _find_social_proof(soup, elements)
    _find_trust_badges(soup, elements)
    _find_price_block(soup, elements)
    _find_benefit_bullets(soup, elements)

    return elements


def merge_mappings(
    url: str,
    dom_elements: dict,
    vision_elements: Optional[dict],
    is_shopify: bool,
    theme_name: Optional[str],
) -> SemanticMap:
    """
    Combine DOM heuristic results with optional vision-assisted bounding boxes
    into a final SemanticMap.
    """
    # Start with DOM results, overlay vision bboxes where available
    if vision_elements:
        for role, el in dom_elements.items():
            if role in vision_elements and vision_elements[role]:
                el.bbox = vision_elements[role].get("bbox")
                if "is_above_the_fold" in vision_elements[role]:
                    el.is_above_the_fold = vision_elements[role]["is_above_the_fold"]

    return SemanticMap(
        url=url,
        hero_section=dom_elements.get("hero"),
        hero_headline=dom_elements.get("hero_headline"),
        hero_subheadline=dom_elements.get("hero_subheadline"),
        hero_image=dom_elements.get("hero_image"),
        primary_cta=dom_elements.get("primary_cta"),
        secondary_cta=dom_elements.get("secondary_cta"),
        announcement_bar=dom_elements.get("announcement_bar"),
        social_proof_blocks=dom_elements.get("social_proof_blocks", []),
        trust_badges=dom_elements.get("trust_badges", []),
        price_block=dom_elements.get("price_block"),
        benefit_bullets=dom_elements.get("benefit_bullets"),
        is_shopify=is_shopify,
        shopify_theme=theme_name,
        page_type=_detect_page_type(url),
    )


async def vision_assisted_mapping(
    screenshot_bytes: Optional[bytes],
    llm_model: str,
) -> Optional[dict]:
    """
    Optional: send the page screenshot to Gemini Flash to identify element bounding boxes.
    Returns a dict of role → {bbox, is_above_the_fold} or None if unavailable.
    """
    if not screenshot_bytes:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client()

        prompt = """Look at this landing page screenshot and identify the bounding boxes
of these elements if present: hero_headline, hero_subheadline, primary_cta, announcement_bar.

Return JSON with this structure:
{
  "hero_headline": {"bbox": {"x": 0, "y": 0, "width": 100, "height": 50}, "is_above_the_fold": true},
  "primary_cta": {"bbox": {"x": 0, "y": 0, "width": 100, "height": 50}, "is_above_the_fold": true}
}

Only include elements you can clearly identify. Return null for missing elements.
Return ONLY valid JSON."""

        response = client.models.generate_content(
            model=llm_model,
            contents=types.Content(
                parts=[
                    types.Part(text=prompt),
                    types.Part(
                        inline_data=types.Blob(mime_type="image/png", data=screenshot_bytes)
                    ),
                ]
            ),
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                response_mime_type="application/json",
            ),
        )

        import json
        return json.loads(response.text)

    except Exception as e:
        print(f"[dom_mapper] Vision assist failed: {e}")
        return None


# ── Private helpers ───────────────────────────────────────────────────────────

def _find_hero(soup: BeautifulSoup, elements: dict, is_shopify: bool) -> None:
    """Locate the hero/banner section and its children."""
    hero_candidates = []

    # Shopify-specific selectors first (highest confidence)
    if is_shopify:
        for sel in get_shopify_hero_selectors():
            found = soup.select(sel)
            hero_candidates.extend(found)

    # Generic: first <section>/<div>/<header> with h1 + button/a CTA
    if not hero_candidates:
        for section in soup.find_all(["section", "div", "header"], limit=20):
            has_heading = section.find(["h1", "h2"])
            has_cta = _find_cta_in(section)
            if has_heading and has_cta:
                hero_candidates.append(section)
                break

    # Fallback: first <section> with an h1
    if not hero_candidates:
        for section in soup.find_all(["section", "header"], limit=10):
            if section.find("h1"):
                hero_candidates.append(section)
                break

    if not hero_candidates:
        return

    hero = hero_candidates[0]
    elements["hero"] = _make_el("hero_section", hero)

    # Hero headline (h1 preferred, then h2)
    h1 = hero.find("h1") or hero.find("h2")
    if h1:
        elements["hero_headline"] = _make_el("hero_headline", h1)

        # Subheadline: next sibling p / h3 after the headline
        for sibling in h1.find_next_siblings(["p", "h2", "h3", "span"]):
            text = sibling.get_text(strip=True)
            if len(text) > 10:
                elements["hero_subheadline"] = _make_el("hero_subheadline", sibling)
                break

    # Hero image
    img = hero.find("img")
    if img:
        elements["hero_image"] = _make_el("hero_image", img)

    # Primary CTA within hero
    cta = _find_cta_in(hero)
    if cta:
        elements["primary_cta"] = _make_el("primary_cta", cta)

    # Secondary CTA (second button if present)
    all_ctas = _find_all_ctas_in(hero)
    if len(all_ctas) > 1:
        elements["secondary_cta"] = _make_el("secondary_cta", all_ctas[1])


def _find_announcement_bar(soup: BeautifulSoup, elements: dict) -> None:
    """Locate the top announcement/promo bar."""
    body = soup.find("body")
    if not body:
        return

    first_children = list(body.children)
    for child in first_children[:5]:
        if not isinstance(child, Tag):
            continue
        classes = " ".join(child.get("class", []))
        text = child.get_text(strip=True)
        if (
            any(kw in classes.lower() for kw in ["announcement", "promo", "top-bar", "ticker", "banner-top"])
            and len(text) < 200
        ):
            elements["announcement_bar"] = _make_el("announcement_bar", child)
            return


def _find_social_proof(soup: BeautifulSoup, elements: dict) -> None:
    """Find social proof elements — star ratings, review counts, testimonials."""
    pattern = re.compile(r"(reviews?|rated|stars?|customers?|testimonial|rating|verified)", re.I)
    blocks = []
    for el in soup.find_all(["div", "section", "span", "p"], limit=50):
        text = el.get_text(strip=True)
        if pattern.search(text) and 5 < len(text) < 300:
            # Avoid duplicating parent/child — only take the most specific element
            blocks.append(_make_el("social_proof_block", el))
            if len(blocks) >= 3:
                break
    if blocks:
        elements["social_proof_blocks"] = blocks


def _find_trust_badges(soup: BeautifulSoup, elements: dict) -> None:
    """Find trust badges — secure checkout, money-back guarantee, etc."""
    trust_pattern = re.compile(
        r"(secure|guarantee|money.back|free.return|ssl|verified|certified|100%)", re.I
    )
    badges = []
    for el in soup.find_all(["div", "span", "img", "p"], limit=60):
        text = el.get_text(strip=True) or el.get("alt", "")
        if trust_pattern.search(text) and len(text) < 150:
            badges.append(_make_el("trust_badge", el))
            if len(badges) >= 4:
                break
    if badges:
        elements["trust_badges"] = badges


def _find_price_block(soup: BeautifulSoup, elements: dict) -> None:
    """Find price display elements."""
    price_pattern = re.compile(r"(₹|Rs\.?|\$|£|price|MRP|off)", re.I)
    for el in soup.find_all(["span", "div", "p"], limit=40):
        text = el.get_text(strip=True)
        if price_pattern.search(text) and len(text) < 100:
            elements["price_block"] = _make_el("price_block", el)
            return


def _find_benefit_bullets(soup: BeautifulSoup, elements: dict) -> None:
    """Find benefit bullet point list (ul/ol near the hero)."""
    for ul in soup.find_all(["ul", "ol"], limit=10):
        items = ul.find_all("li")
        if 2 <= len(items) <= 8:
            text = ul.get_text(strip=True)
            if len(text) > 20:
                elements["benefit_bullets"] = _make_el("benefit_bullets", ul)
                return


def _find_cta_in(section: Tag) -> Optional[Tag]:
    """Find the primary CTA button or link within a section."""
    cta_classes = re.compile(r"(btn|button|cta|primary|shop|buy|get|try)", re.I)
    for tag in section.find_all(["button", "a"], limit=10):
        classes = " ".join(tag.get("class", []))
        text = tag.get_text(strip=True)
        if cta_classes.search(classes) or (len(text) > 2 and len(text) < 40):
            return tag
    return None


def _find_all_ctas_in(section: Tag) -> list[Tag]:
    """Find all CTA-like buttons/links within a section."""
    cta_classes = re.compile(r"(btn|button|cta|primary|secondary|shop|buy|get)", re.I)
    results = []
    for tag in section.find_all(["button", "a"], limit=10):
        classes = " ".join(tag.get("class", []))
        text = tag.get_text(strip=True)
        if cta_classes.search(classes) and 2 < len(text) < 40:
            results.append(tag)
    return results


def _make_el(role: str, element: Tag) -> PageElement:
    """Create a PageElement from a BeautifulSoup element."""
    return PageElement(
        role=role,
        selector=_generate_selector(element),
        text=element.get_text(strip=True)[:500] if element else None,
        html=str(element)[:2000],
        importance=_importance(role),
    )


def _generate_selector(element: Tag) -> str:
    """Generate a CSS selector — id > unique class combo > tag path."""
    if element.get("id"):
        return f"#{element['id']}"

    classes = element.get("class", [])
    if classes:
        tag = element.name
        class_sel = ".".join(classes[:3])
        return f"{tag}.{class_sel}"

    # Build a short ancestor path
    parts = []
    current = element
    for _ in range(4):
        if not current or current.name in ("[document]", "html", "body"):
            break
        if current.get("id"):
            parts.insert(0, f"#{current['id']}")
            break
        tag = current.name
        parent = current.parent
        if parent:
            siblings = [s for s in parent.children if isinstance(s, Tag) and s.name == tag]
            if len(siblings) > 1:
                idx = siblings.index(current) + 1
                parts.insert(0, f"{tag}:nth-of-type({idx})")
            else:
                parts.insert(0, tag)
        current = parent

    return " > ".join(parts) if parts else element.name


def _importance(role: str) -> float:
    """Heuristic importance weights for CRO prioritization."""
    return {
        "hero_section": 1.0, "hero_headline": 1.0, "hero_subheadline": 0.9,
        "primary_cta": 0.95, "secondary_cta": 0.6, "announcement_bar": 0.7,
        "social_proof_block": 0.8, "trust_badge": 0.7, "hero_image": 0.85,
        "price_block": 0.85, "benefit_bullets": 0.75, "other": 0.2,
    }.get(role, 0.5)


def _detect_page_type(url: str) -> Optional[str]:
    """Infer page type from URL patterns."""
    url_lower = url.lower()
    if any(k in url_lower for k in ["/products/", "/product/", "/p/"]):
        return "product"
    if any(k in url_lower for k in ["/collections/", "/category/", "/shop/"]):
        return "collection"
    if url_lower.rstrip("/").split("//")[-1].count("/") == 0:
        return "homepage"
    if any(k in url_lower for k in ["/lp/", "/landing/", "/offer/", "/sale/"]):
        return "landing"
    return "other"
