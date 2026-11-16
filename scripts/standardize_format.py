import os
import re
import json

TRANSCRIPTIONS_DIR = "transcriptions"
MANIFEST_PATH = "manifest.json"

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

img_name_map = {}
for item in manifest["items"]:
    base_id = item["id"] # e.g. IMG_0465
    img_name_map[base_id] = item["filename"] # e.g. IMG_0465_rotated_90.jpg

def parse_and_reformat(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    base_id = os.path.basename(filepath).replace(".md", "")
    img_filename = img_name_map.get(base_id, f"{base_id}_rotated_90.jpg")

    # If already fully formatted with "## Metadata" and sub-bullets, skip or ensure exact format
    has_metadata_header = "## Metadata" in content
    has_sub_bullets = "- **Key Entities (Persons):**" in content

    # Extract sections
    # Extract header / metadata
    source_doc = ""
    archive_ref = ""
    date_range = ""
    key_events = ""
    subject = ""

    m = re.search(r"\*\*Source Document:\*\*\s*(.*?)\s*\n", content)
    if m: source_doc = m.group(1).strip()
    m = re.search(r"\*\*Archive Reference:\*\*\s*(.*?)\s*\n", content)
    if m: archive_ref = m.group(1).strip()
    m = re.search(r"\*\*Date Range:\*\*\s*(.*?)\s*\n", content)
    if m: date_range = m.group(1).strip()
    m = re.search(r"\*\*Key Events & Entities:\*\*\s*(.*?)\s*\n", content)
    if m: key_events = m.group(1).strip()
    m = re.search(r"\*\*Subject:\*\*\s*(.*?)\s*\n", content)
    if m: subject = m.group(1).strip()

    # If already has - **Source:** etc:
    m = re.search(r"-\s*\*\*Source:\*\*\s*(.*?)\s*\n", content)
    if m: source_val = m.group(1).strip()
    else:
        if archive_ref and source_doc:
            source_val = f"Peter Carey Collection / Archival Research Notes ({archive_ref}: {source_doc})"
        elif archive_ref:
            source_val = f"Peter Carey Collection / Archival Research Notes ({archive_ref})"
        elif source_doc:
            source_val = f"Peter Carey Collection / Archival Research Notes ({source_doc})"
        else:
            source_val = "Peter Carey Collection / Archival Research Notes"

    m = re.search(r"-\s*\*\*Date Range:\*\*\s*(.*?)\s*\n", content)
    if m: date_range = m.group(1).strip()

    # Extract Cross-Reference entities to populate Persons, Places, Institutions/Terms
    people_list = []
    places_list = []
    terms_list = []

    people_match = re.search(r"\*\s*\*\*People:\*\*(.*?)(?=\n\*\s*\*\*|\n---|\Z)", content, re.DOTALL)
    if people_match:
        for line in people_match.group(1).strip().split("\n"):
            pm = re.search(r"\*\s*\*\*(.*?)\*\*", line)
            if pm:
                name = pm.group(1).strip()
                # clean up titles if wanted, or keep canonical
                people_list.append(name)

    places_match = re.search(r"\*\s*\*\*(?:Places|Places & Institutions):\*\*(.*?)(?=\n\*\s*\*\*|\n---|\Z)", content, re.DOTALL)
    if places_match:
        for line in places_match.group(1).strip().split("\n"):
            pm = re.search(r"\*\s*\*\*(.*?)\*\*", line)
            if pm:
                places_list.append(pm.group(1).strip())

    terms_match = re.search(r"\*\s*\*\*(?:Terms|Terms & Concepts|Terms, Units, & Concepts):\*\*(.*?)(?=\n\*\s*\*\*|\n---|\Z)", content, re.DOTALL)
    if terms_match:
        for line in terms_match.group(1).strip().split("\n"):
            pm = re.search(r"\*\s*\*\*(.*?)\*\*", line)
            if pm:
                terms_list.append(pm.group(1).strip())

    # Build Key Events text
    if not key_events:
        m = re.search(r"-\s*\*\*Key Events:\*\*\s*(.*?)\s*\n", content)
        if m: key_events = m.group(1).strip()
        elif subject: key_events = subject
        else: key_events = "Archival notes and documentation."

    # Blank verso check
    is_blank = "blank verso" in content.lower() or "blank page" in content.lower()
    if is_blank and "N/A" in date_range:
        persons_str = "None (blank verso)"
        places_str = "None (blank verso)"
        terms_str = "None (blank verso)"
    else:
        persons_str = ", ".join(people_list) if people_list else "None recorded"
        places_str = ", ".join(places_list) if places_list else "None recorded"
        terms_str = ", ".join(terms_list) if terms_list else "None recorded"

    # Now extract the remainder of the document from Header & Archival Classification onwards
    header_idx = content.find("### Header & Archival Classification")
    if header_idx != -1:
        body = content[header_idx:].strip()
    else:
        # fallback
        sep = content.find("---")
        if sep != -1:
            body = content[sep+3:].strip()
        else:
            body = content

    # Ensure cross reference section headers match:
    # * **Places & Institutions:**
    # * **Terms:**
    body = re.sub(r"\*\s*\*\*Places:\*\*", r"* **Places & Institutions:**", body)
    body = re.sub(r"\*\s*\*\*Terms & Concepts:\*\*", r"* **Terms:**", body)
    body = re.sub(r"\*\s*\*\*Terms, Units, & Concepts:\*\*", r"* **Terms:**", body)

    new_content = f"""# Transcription of {img_filename}

## Metadata
- **Image File:** `jpg/{img_filename}`
- **Source:** {source_val}
- **Date Range:** {date_range}
- **Key Events & Entities:**
  - **Key Events:** {key_events}
  - **Key Entities (Persons):** {persons_str}
  - **Key Entities (Places):** {places_str}
  - **Key Entities (Institutions / Terms):** {terms_str}

---

{body}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Standardized {filepath}")

if __name__ == "__main__":
    for fname in sorted(os.listdir(TRANSCRIPTIONS_DIR)):
        if fname.endswith(".md"):
            parse_and_reformat(os.path.join(TRANSCRIPTIONS_DIR, fname))
