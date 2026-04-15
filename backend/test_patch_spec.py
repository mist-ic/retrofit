"""Quick local test: validate that PatchSpec sanitization handles all LLM quirks."""

import json
from app.models.patch_spec import PatchSpec, sanitize_operations

# Simulated LLM outputs that have caused production crashes
test_cases = [
    # Case 1: LLM uses "content" instead of "html"
    {
        "variant_id": "test-1",
        "description": "Content alias test",
        "operations": [
            {"op": "replaceText", "selector": "h1", "new_text": "Hello"},
            {"op": "insertAfter", "selector": ".hero", "content": "<div>50% OFF</div>"},
        ],
    },
    # Case 2: LLM uses "new_html" instead of "html"
    {
        "variant_id": "test-2",
        "description": "new_html alias test",
        "operations": [
            {"op": "insertBefore", "selector": ".hero", "new_html": "<div>Banner</div>"},
        ],
    },
    # Case 3: LLM omits html entirely
    {
        "variant_id": "test-3",
        "description": "Missing html test",
        "operations": [
            {"op": "insertAfter", "selector": ".hero"},
        ],
    },
    # Case 4: LLM uses "markup"
    {
        "variant_id": "test-4",
        "description": "markup alias test",
        "operations": [
            {"op": "insertAfter", "selector": ".cta", "markup": "<span>Limited Time!</span>"},
        ],
    },
    # Case 5: Correct usage — should pass as-is
    {
        "variant_id": "test-5",
        "description": "Correct html usage",
        "operations": [
            {"op": "insertAfter", "selector": ".hero", "html": "<div>Promo</div>"},
            {"op": "replaceText", "selector": "h1", "new_text": "Sale!"},
            {"op": "replaceStyle", "selector": "a.btn", "css_text": "color: red;"},
        ],
    },
    # Case 6: replaceStyle with "style" alias
    {
        "variant_id": "test-6",
        "description": "style alias test",
        "operations": [
            {"op": "replaceStyle", "selector": ".btn", "style": "background: blue;"},
        ],
    },
]

print("=" * 70)
print("PatchSpec Sanitization Tests")
print("=" * 70)

for i, tc in enumerate(test_cases, 1):
    try:
        patch = PatchSpec.model_validate(tc)
        print(f"\n✅ Case {i}: {tc['description']}")
        for op in patch.operations:
            d = op.model_dump()
            op_type = d["op"]
            if op_type in ("insertBefore", "insertAfter"):
                print(f"   {op_type} → html={d['html'][:60]}...")
            elif op_type == "replaceStyle":
                print(f"   {op_type} → css_text={d['css_text']}")
            elif op_type == "replaceText":
                print(f"   {op_type} → new_text={d['new_text']}")
            else:
                print(f"   {op_type}")
    except Exception as e:
        print(f"\n❌ Case {i}: {tc['description']}")
        print(f"   ERROR: {e}")

print("\n" + "=" * 70)
print("All tests complete.")
