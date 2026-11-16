import re
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
INDEX_FILE = WORKSPACE_DIR / "39_Expanded_Keyword_Index.md"
TRANSCRIPTIONS_DIR = WORKSPACE_DIR / "transcriptions"

def load_canonical_keywords():
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract bold items: e.g. **Dipanagara, Prince (Pangéran Dipanagara)**
    bold_pattern = re.compile(r'\*\*(.+?)\*\*')
    entities = set()
    for match in bold_pattern.finditer(text):
        raw = match.group(1).strip()
        # split by parentheses, slashes, commas
        subparts = re.split(r'[,/()]', raw)
        for part in subparts:
            cleaned = part.strip()
            if len(cleaned) > 2 and not cleaned.startswith("Appendix") and not cleaned.startswith("Chapter"):
                entities.add(cleaned)
    return entities

def validate_transcriptions():
    entities = load_canonical_keywords()
    print(f"Loaded {len(entities)} canonical entities/terms from keyword index.")

    md_files = sorted(TRANSCRIPTIONS_DIR.glob("*.md"))
    print(f"Validating {len(md_files)} transcription files...")

    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        matched = []
        for ent in sorted(entities, key=len, reverse=True):
            if re.search(r'\b' + re.escape(ent) + r'\b', content, re.IGNORECASE):
                matched.append(ent)

        # deduplicate case-insensitively
        seen = set()
        deduped = []
        for m in matched:
            low = m.lower()
            if low not in seen:
                seen.add(low)
                deduped.append(m)

        print(f"\n[{md_file.name}] - Found {len(deduped)} entity matches:")
        for m in deduped[:10]:
            print(f"  * {m}")
        if len(deduped) > 10:
            print(f"  ... and {len(deduped) - 10} more.")

from audit_corpus import audit_and_fix

if __name__ == "__main__":
    validate_transcriptions()
    print("\n--- Running Strict Line-Citation Audit ---")
    mismatches = audit_and_fix(fix=False)
    if mismatches > 0:
        raise SystemExit(1)
