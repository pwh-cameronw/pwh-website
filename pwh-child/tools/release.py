"""Bump the theme version and build ../pwh-child.zip for uploading to WordPress.

    python3 tools/release.py          # 1.2.3 -> 1.2.4
    python3 tools/release.py minor    # 1.2.3 -> 1.3.0
    python3 tools/release.py 2.0.0    # set an exact version

The version is kept in style.css (shown in Appearance > Themes) and
PWH_CHILD_VERSION in functions.php.
"""
import os
import re
import subprocess
import sys

THEME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STYLE = os.path.join(THEME, "style.css")
FUNCTIONS = os.path.join(THEME, "functions.php")


def bump(version, how):
    if re.fullmatch(r"\d+\.\d+\.\d+", how):
        return how
    major, minor, patch = map(int, version.split("."))
    if how == "major":
        return f"{major + 1}.0.0"
    if how == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def main():
    with open(STYLE, encoding="utf-8") as fh:
        style = fh.read()
    old = re.search(r"^Version:\s*(\S+)", style, re.M).group(1)
    new = bump(old, sys.argv[1] if len(sys.argv) > 1 else "patch")

    with open(STYLE, "w", encoding="utf-8") as fh:
        fh.write(re.sub(r"^(Version:\s*)\S+", r"\g<1>" + new, style, count=1, flags=re.M))
    with open(FUNCTIONS, encoding="utf-8") as fh:
        functions = fh.read()
    with open(FUNCTIONS, "w", encoding="utf-8") as fh:
        fh.write(re.sub(r"(define\( 'PWH_CHILD_VERSION', ')[^']*(' \);)", r"\g<1>" + new + r"\g<2>", functions, count=1))

    root = os.path.abspath(os.path.join(THEME, ".."))
    zip_path = os.path.join(root, "pwh-child.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    subprocess.run(["zip", "-qr", zip_path, "pwh-child", "-x", "*/__pycache__/*", "*.pyc"], cwd=root, check=True)
    print(f"pwh-child {old} -> {new}: {zip_path}")


if __name__ == "__main__":
    main()
