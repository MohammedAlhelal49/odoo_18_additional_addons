#!/usr/bin/env python3
"""
Downloads every /web/image/... asset referenced in app_data.py and
industry_data.py from the LIVE dekad.tech site, saves each one into a
folder structure organized by PAGE and FIELD (not a flat list of
hashed filenames), and rewrites the data files to point to the new
local paths instead of the original attachment URLs.

RESULTING FOLDER LAYOUT
------------------------
static/src/img/migrated/
    apps/
        accounting-finance/
            cover_bg.png
            overview_image.png
            key_features_image_1.png
            key_features_image_2.png
            ...
        crm/
            cover_bg.png
            ...
    industries/
        education/
            hero_bg_image.png
            showcase_image.webp
            cards_image_1.png
            masonry_image.jpg
        manufacturing/
            ...

Each folder = one app or one industry (matches the slug used in its
URL, e.g. /apps/accounting-finance or /industries/education), and each
file name tells you exactly which field it fills - so it's easy to
find "the cover image for the CRM app page" or "the 2nd key-feature
image for Accounting & Invoicing" and swap it out by hand later.

USAGE
-----
1. Copy this script into the root of the dekad_website module
   (next to __manifest__.py), on a machine that has normal internet
   access to https://dekad.tech.
2. Install the one dependency:
       pip install requests --break-system-packages
3. Run it:
       python3 migrate_images.py
4. Review the new static/src/img/migrated/ folder and the updated
   data/app_data.py + data/industry_data.py, then -u dekad_website.

WHY THIS RUNS ON YOUR MACHINE, NOT IN THE CHAT SANDBOX
--------------------------------------------------------
The assistant's own sandbox can only reach a small allow-list of
domains (github, pypi, npm, etc.) and dekad.tech is not on it, so the
actual downloading has to happen from a machine that does have normal
access to your site.
"""
import os
import re
import sys

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run: pip install requests --break-system-packages")

# --- Configuration ---------------------------------------------------
SITE_BASE = "https://dekad.tech"          # change if testing on a staging URL

# Each entry: (data file, output subfolder under static/src/img/migrated/)
DATA_FILES = [
    (os.path.join("data", "app_data.py"), "apps"),
    (os.path.join("data", "industry_data.py"), "industries"),
    (os.path.join("data", "service_data.py"), "services"),
]

MIGRATED_ROOT = os.path.join("static", "src", "img", "migrated")

# Matches a top-level dict entry key, e.g.  '    'accounting-finance': {'
TOP_LEVEL_KEY_RE = re.compile(r"^\s{4}'([\w\-]+)':\s*\{\s*$")

# Matches   'some_field': '/anything/ending/in/an/image/extension'
# Covers both attachment-style URLs (/web/image/...) and static module
# asset paths (/dekad_website/static/src/img/...) - any absolute path
# ending in a known image extension.
FIELD_IMAGE_RE = re.compile(
    r"'(\w+)':\s*'(/[A-Za-z0-9_\-./%]+\.(?:png|jpg|jpeg|webp|gif|svg))'"
)

# ----------------------------------------------------------------------


def guess_extension(content_type, url):
    if content_type:
        content_type = content_type.split(";")[0].strip().lower()
        mapping = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/svg+xml": ".svg",
        }
        if content_type in mapping:
            return mapping[content_type]
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"):
        if url.lower().endswith(ext):
            return ext
    return ".jpg"


def download(url, dest_path):
    full_url = SITE_BASE + url
    resp = requests.get(full_url, timeout=20)
    resp.raise_for_status()
    ext = guess_extension(resp.headers.get("Content-Type"), url)
    dest_path_with_ext = dest_path + ext
    os.makedirs(os.path.dirname(dest_path_with_ext), exist_ok=True)
    with open(dest_path_with_ext, "wb") as out:
        out.write(resp.content)
    return dest_path_with_ext


def process_file(path, subfolder):
    if not os.path.exists(path):
        print(f"  (skipping {path}, not found)")
        return

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    current_slug = None
    field_counters = {}   # (slug, field_name) -> next index, for repeated fields (e.g. list items)
    url_to_local = {}      # original /web/image/... path -> new local site-relative URL
    failed = []
    total_found = 0
    already_migrated = 0

    for line in lines:
        top_match = TOP_LEVEL_KEY_RE.match(line)
        if top_match:
            current_slug = top_match.group(1)
            continue

        for field_name, img_url in FIELD_IMAGE_RE.findall(line):
            total_found += 1

            # Already migrated in a previous run (points at our own
            # module's static folder) - never re-fetch these, and never
            # try to download from dekad.tech using a path that only
            # exists locally.
            if img_url.startswith("/dekad_website/"):
                already_migrated += 1
                continue

            if img_url in url_to_local:
                continue  # already downloaded/named from an earlier occurrence

            slug = current_slug or "misc"
            key = (slug, field_name)
            field_counters[key] = field_counters.get(key, 0) + 1
            count = field_counters[key]
            suffix = "" if count == 1 else f"_{count}"
            dest_base = os.path.join(MIGRATED_ROOT, subfolder, slug, f"{field_name}{suffix}")

            try:
                saved_path = download(img_url, dest_base)
            except Exception as exc:
                print(f"  FAILED [{slug}] {field_name} -> {exc}")
                failed.append(img_url)
                continue

            # Convert filesystem path to the site-relative URL Odoo will serve
            rel = saved_path.replace(os.sep, "/")
            new_url = f"/dekad_website/{rel}"
            url_to_local[img_url] = new_url
            print(f"  OK [{slug}] {field_name} -> {new_url}")

    if not url_to_local:
        if already_migrated:
            print(f"  All {already_migrated} image(s) in {path} are already migrated - nothing to do.")
        else:
            print(f"  No images found/downloaded in {path}.")
        return

    content = "".join(lines)
    for old_url, new_url in url_to_local.items():
        content = content.replace(old_url, new_url)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n  {path}: {len(url_to_local)}/{total_found} unique image(s) downloaded and rewritten"
          f" ({already_migrated} already migrated, skipped).")
    if failed:
        print(f"  {len(failed)} failed:")
        for u in failed:
            print(f"    - {u}")


def main():
    if not os.path.isdir("data"):
        sys.exit("Run this from the dekad_website module root (data/ not found here).")

    for path, subfolder in DATA_FILES:
        print(f"\n=== Processing {path} ===")
        process_file(path, subfolder)

    print("\nDone. Review static/src/img/migrated/ then -u dekad_website.")


if __name__ == "__main__":
    main()