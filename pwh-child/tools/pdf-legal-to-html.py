"""Turn a numbered legal PDF (pdftotext -layout output) into clean HTML.

Sections "1.  Title" become <h3>, clauses "1.1.  Text" become numbered
paragraphs, "a. Text" items become lettered lists. Wording is kept exactly;
emails and URLs are linked. Page footers ("© ... Page n of m") are dropped.

Usage: python3 pdf-legal-to-html.py input.txt START_LINE > out.html
"""
import html
import re
import sys

SECTION = re.compile(r"^\s{0,4}(\d{1,2})\.\s+([A-Z0-9]\S.*)$")
CLAUSE = re.compile(r"^\s*(\d{1,2}\.\d{1,2})\.\s+(\S.*)$")
ITEM = re.compile(r"^\s*([a-z])\.\s+(\S.*)$")
FOOTER = re.compile(r"\bPage \d+ of \d+\b")
LINK = re.compile(r"(?<!\()(https?://[^\s<]+[^\s<.,)]|[\w.+-]+@[\w-]+(?:\.[\w-]+)+)")


def linkify(text):
    def rep(m):
        u = m.group(1)
        href = "mailto:" + u if "@" in u and not u.startswith("http") else u
        return f'<a href="{href}">{u}</a>'
    return LINK.sub(rep, html.escape(text, quote=False))


def main(path, start):
    lines = open(path, encoding="utf-8").read().splitlines()[start - 1:]
    blocks = []  # (kind, num, text)
    cur = None
    blank = False
    page_break = False
    for raw in lines:
        if raw.strip().startswith("©") or FOOTER.search(raw):
            page_break = True
            continue
        if not raw.strip():
            blank = True
            continue
        indent = len(raw) - len(raw.lstrip())
        text = raw.strip()
        m = SECTION.match(raw)
        if m and not CLAUSE.match(raw):
            cur = ["h", m.group(1), m.group(2)]
        elif CLAUSE.match(raw):
            m = CLAUSE.match(raw)
            cur = ["c", m.group(1), m.group(2)]
        elif ITEM.match(raw) and indent >= 20:
            m = ITEM.match(raw)
            cur = ["i", m.group(1), m.group(2)]
        elif cur and (not blank or page_break):
            # Wrapped line (possibly across a page break). A line ending in a
            # hyphen splits a compound like "time-to-time": join without a space.
            cur[2] += ("" if re.search(r"\w-$", cur[2]) else " ") + text
            page_break = False
            blank = False
            continue
        elif cur and cur[0] == "i" and indent >= 15:
            cur = ["p2", "", text]  # paragraph continuing a clause after its list
        else:
            cur = ["p", "", text]
        blocks.append(cur)
        blank = False
        page_break = False

    out, in_list = [], False
    for kind, num, text in blocks:
        text = " ".join(text.split())
        if kind != "i" and in_list:
            out.append("</ol>")
            in_list = False
        if kind == "h":
            out.append(f"<h3>{num}. {linkify(text)}</h3>")
        elif kind == "c":
            out.append(f'<p class="pwh-l-clause"><span class="pwh-l-num">{num}.</span> {linkify(text)}</p>')
        elif kind == "i":
            if not in_list:
                out.append('<ol class="pwh-l-items" type="a">')
                in_list = True
            out.append(f"<li>{linkify(text)}</li>")
        elif kind == "p2":
            out.append(f'<p class="pwh-l-clause pwh-l-cont">{linkify(text)}</p>')
        else:
            out.append(f"<p>{linkify(text)}</p>")
    if in_list:
        out.append("</ol>")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
