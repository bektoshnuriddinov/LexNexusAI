"""Test script to verify superscript normalization logic."""
import re
import sys
import io

# Force UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def normalize_text(text: str) -> str:
    """Normalize extracted text to handle legal document notation."""
    if not text:
        return text

    # Superscript to regular number mapping
    superscript_map = {
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
    }

    # Match number followed by one or more superscripts
    pattern = r'(\d+)([⁰¹²³⁴⁵⁶⁷⁸⁹]+)'

    def replace_superscript(match):
        base_num = match.group(1)
        superscripts = match.group(2)
        # Convert superscripts to regular numbers
        regular_nums = ''.join(superscript_map.get(s, s) for s in superscripts)
        # Keep original and add normalized version
        return f"{base_num}{superscripts} ({base_num}-{regular_nums})"

    # Run replacement once on entire text
    normalized = re.sub(pattern, replace_superscript, text)
    return normalized

# Test cases
test_cases = [
    ("Article 497²⁶", "Article 497²⁶ (497-26)"),
    ("509⁶", "509⁶ (509-6)"),
    ("Text with 123⁴⁵ multiple", "Text with 123⁴⁵ (123-45) multiple"),
    ("No superscripts here", "No superscripts here"),
]

print("Testing normalize_text() function:\n")
all_passed = True
for input_text, expected in test_cases:
    result = normalize_text(input_text)
    passed = expected in result
    status = "[PASS]" if passed else "[FAIL]"
    if not passed:
        all_passed = False
    print(f"{status} Input:    {repr(input_text)}")
    print(f"        Expected: {repr(expected)}")
    print(f"        Got:      {repr(result)}")
    print()

if all_passed:
    print("[SUCCESS] All tests passed!")
else:
    print("[ERROR] Some tests failed!")
