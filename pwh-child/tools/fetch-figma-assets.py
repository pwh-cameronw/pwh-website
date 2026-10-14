#!/usr/bin/env python3
"""
Downloads every image and icon the theme uses from the Figma file into assets/.

  1. Create a personal access token: Figma → Settings → Security →
     Personal access tokens (scope: File content, read-only).
  2. FIGMA_TOKEN=figd_xxx python3 tools/fetch-figma-assets.py

Photos are fetched as the original uploaded image (not a cropped render) so
they stay sharp; icons and logos are exported as SVG.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

FILE_KEY = "i4OddJr6teWRSoThGo59O3"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

# Photos: node whose image fill is the photo.
PHOTOS = {
    "images/hero-laptop.png": "205:3156",            # Page / Home → cc-website-header 1
    "images/card-domains.png": "14:140",             # Products → Card / Media (Domains)
    "images/card-hosting.png": "14:128",             # Card / Media (Website Hosting)
    "images/card-email.png": "14:134",               # Card / Media (Business Email)
    "images/why-pwh.png": "14:146",                  # WhyPWH section background
    "images/not-sure-cta.png": "231:3435",           # NotSureCTA → 2026_PWH_BRANDSHOOT_NH-1
    "images/avatar-placeholder.png": "6:19",         # Testimonial Card → Ellipse
    "images/logo-light.png": "55:378",               # Footer → image 1
}

# Vectors: exported as SVG.
VECTORS = {
    "images/logo-dark.svg": "46:121",                # Nav → PWH_HORIZONTAL_DUOTONE_DARK 1
    "icons/arrow-right.svg": "23:141",               # Card / Media → ArrowRow
    "icons/stars.svg": "59:988",                     # Testimonial Card → stars
    "icons/location-pin.svg": "331:1650",            # Footer → address icon
    "icons/phone.svg": "232:3541",                   # Footer → phone icon
    "icons/clock.svg": "232:3715",                   # Footer → hours icon
    "icons/facebook.svg": "55:610",                  # Footer → FACEBOOK
    "icons/linkedin.svg": "55:586",                  # Footer → LINKEDIN
    "icons/credit.svg": "55:415",                    # Footer → Layer_1 (Website by)
}


def api(path, token):
    req = urllib.request.Request("https://api.figma.com/v1/" + path, headers={"X-Figma-Token": token})
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with urllib.request.urlopen(url) as res, open(dest, "wb") as fh:
        fh.write(res.read())
    print(f"  {os.path.relpath(dest, ROOT)}  ({os.path.getsize(dest):,} bytes)")


def main():
    token = os.environ.get("FIGMA_TOKEN")
    if not token:
        sys.exit("Set FIGMA_TOKEN to a Figma personal access token.")

    print("Photos")
    ids = ",".join(PHOTOS.values())
    nodes = api(f"files/{FILE_KEY}/nodes?ids={urllib.parse.quote(ids)}", token)["nodes"]
    fills = api(f"files/{FILE_KEY}/images", token)["meta"]["images"]
    for dest, node_id in PHOTOS.items():
        doc = (nodes.get(node_id) or {}).get("document") or {}
        refs = [f.get("imageRef") for f in doc.get("fills", []) if f.get("type") == "IMAGE"]
        if not refs or refs[-1] not in fills:
            print(f"  ! no image fill on {node_id} for {dest}")
            continue
        download(fills[refs[-1]], os.path.join(ROOT, dest))

    print("Vectors")
    ids = ",".join(VECTORS.values())
    urls = api(f"images/{FILE_KEY}?ids={urllib.parse.quote(ids)}&format=svg&svg_include_id=false", token)["images"]
    for dest, node_id in VECTORS.items():
        if not urls.get(node_id):
            print(f"  ! export failed for {node_id} ({dest})")
            continue
        download(urls[node_id], os.path.join(ROOT, dest))


if __name__ == "__main__":
    main()
