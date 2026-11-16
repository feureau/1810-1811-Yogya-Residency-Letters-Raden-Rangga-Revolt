import json
from pathlib import Path
from PIL import Image

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
JPG_DIR = WORKSPACE_DIR / "jpg"
TRANSCRIPTIONS_DIR = WORKSPACE_DIR / "transcriptions"
MANIFEST_FILE = WORKSPACE_DIR / "manifest.json"

KNOWN_SPECIAL_TYPES = {
    "IMG_0461_rotated_90.jpg": ("calibration", "ColorChecker target"),
    "IMG_0462_rotated_90.jpg": ("calibration", "Focus / exposure chart"),
    "IMG_0463_rotated_90.jpg": ("calibration", "Flat field vignette reference"),
    "IMG_0464_rotated_90.jpg": ("cover", "Grey archival folder cover labeled '1810'"),
    "IMG_0465_rotated_90.jpg": ("explanatory_note", "Typewritten note on Daendels agricultural month names"),
    "IMG_0875_rotated_90.jpg": ("cover", "Pink archival divider folder labeled '1829'"),
    "IMG_0877_rotated_90.jpg": ("cover", "Binder spine label 'Yogya Residency Letters 1810 - 1811 Raden Rangga Revolt II'"),
}

def build_manifest():
    files = sorted(JPG_DIR.glob("*.jpg"), key=lambda p: p.name)
    print(f"Found {len(files)} image files in {JPG_DIR}")

    items = []
    completed_count = 0
    skipped_count = 0
    pending_count = 0

    for idx, f in enumerate(files, 1):
        filename = f.name
        img_id = filename.split("_rotated")[0]
        md_name = f"{img_id}.md"
        md_path = TRANSCRIPTIONS_DIR / md_name

        category, description = KNOWN_SPECIAL_TYPES.get(filename, ("research_notes", "Handwritten notebook page"))

        if md_path.exists():
            status = "completed"
            completed_count += 1
        elif category in ("calibration", "cover"):
            status = "skipped"
            skipped_count += 1
        else:
            status = "pending"
            pending_count += 1

        # Read dimensions
        try:
            with Image.open(f) as img:
                width, height = img.size
        except Exception as e:
            width, height = None, None

        item = {
            "index": idx,
            "filename": filename,
            "id": img_id,
            "width": width,
            "height": height,
            "filesize_bytes": f.stat().st_size,
            "category": category,
            "description": description,
            "status": status,
            "transcription_file": f"transcriptions/{md_name}" if md_path.exists() else None
        }
        items.append(item)

    manifest_data = {
        "total_images": len(items),
        "status_counts": {
            "completed": completed_count,
            "pending": pending_count,
            "skipped": skipped_count
        },
        "items": items
    }

    with open(MANIFEST_FILE, "w", encoding="utf-8") as out:
        json.dump(manifest_data, out, indent=2)

    print(f"Manifest written to {MANIFEST_FILE}")
    print(f"Summary: Completed={completed_count}, Pending={pending_count}, Skipped={skipped_count}")

    # Synchronize site data.json
    try:
        from build_site_data import build_site_data
    except ImportError:
        import sys
        sys.path.append(str(Path(__file__).resolve().parent))
        from build_site_data import build_site_data
    build_site_data()

if __name__ == "__main__":
    build_manifest()
