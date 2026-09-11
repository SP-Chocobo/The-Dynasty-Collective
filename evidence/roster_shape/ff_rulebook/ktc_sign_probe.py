"""#148 -- does the INSTRUMENT drop the minus sign, or was one never printed?

`term_lifetimes.UNSIGNED_TREND` records the cause as a HYPOTHESIS: "the site renders
direction as a coloured arrow glyph rather than a '-' character, so the magnitude survives
extraction and the sign does not." Two things upstream of the CSV could each produce the
observed all-positive column, and the record does not separate them:

    (a) pypdf's extract_text() drops a '-' that IS present in the page's text content, or
    (b) KTC's page never emits a '-' character at all.

The repo's own parser is already ruled out by construction and by history: `_KTC_ROW_RE`
captures the trend as `(-?\\d+)` and `parse_keeptradecut_pdf` converts it with `int()`, and
`git show` confirms that exact regex was in place at BOTH commits that produced the committed
CSV (32e6991, 98e2df1). A sign-capable parser produced 499 unsigned rows.

PRE-REGISTERED PREDICTION, written before running. Fork (a) is the one I can test here without
the source PDFs, because it is a property of the library rather than of KTC. I expect pypdf to
ROUND-TRIP the minus sign -- it is an ordinary glyph in the content stream, not a layout
artifact -- which would leave (b) as the only surviving explanation and make #148 a genuine
input defect rather than a repairable parsing one.

WHAT WOULD FALSIFY THAT: extract_text() returning "12" for text written as "-12". That would
make #148 an in-repo INSTRUMENT defect, re-parseable from PDFs the owner still holds, and would
move it out of BLOCKED-EXTERNAL entirely.

The PDF is hand-built rather than produced by reportlab (not installed here), so the content
stream is visible in this file and nothing is taken on trust from a generator.
"""
from pathlib import Path
import sys

import pypdf

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# The exact shapes in question: a bare negative, the row tail as KTC prints it, and a control.
LINES = ["-12", "Sample Player WR7 T3 45671 -12", "Sample Player WR7 T3 45671 12"]


def _minimal_pdf(lines: list[str]) -> bytes:
    """One page, Helvetica, one Tj per line. Hand-assembled with a real xref table."""
    text_ops = ["BT", "/F1 14 Tf", "72 720 Td", "18 TL"]
    for line in lines:
        escaped = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        text_ops.append(f"({escaped}) Tj")
        text_ops.append("T*")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    return bytes(out)


def main() -> None:
    target = Path(__file__).with_name("ktc_sign_probe.pdf")
    target.write_bytes(_minimal_pdf(LINES))

    extracted = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(target)).pages)
    got = [ln.strip() for ln in extracted.split("\n") if ln.strip()]

    print(f"pypdf            : {pypdf.__version__}")
    print(f"lines written    : {LINES}")
    print(f"lines extracted  : {got}")
    print()

    survived = all(written in got for written in LINES)
    print(f"ROUND-TRIPPED    : {survived}")
    print(f"minus in output  : {'-' in extracted}")

    # Does the repo's own row regex read the sign back off the extracted text?
    import data_merger as dm
    for line in got:
        m = dm._KTC_ROW_RE.match(line)
        if m:
            print(f"  regex on {line!r:50s} -> trend {int(m.groups()[5]):+d}")

    print()
    if survived:
        print("VERDICT: fork (a) FALSIFIED. pypdf preserves the sign and the repo regex reads")
        print("         it back. The instrument is exonerated; (b) is the only survivor --")
        print("         no '-' was ever in the page's text. #148 stays an INPUT defect.")
    else:
        print("VERDICT: fork (a) CONFIRMED -- the instrument drops the sign. #148 is")
        print("         re-parseable in-repo from the PDFs the owner still holds.")


if __name__ == "__main__":
    main()
