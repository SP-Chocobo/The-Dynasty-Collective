"""Render the v2 audit corpus to one PDF the owner can read away from the repo.

Committed so the deliverable is REPRODUCIBLE, not because the PDF is the record: the record is
the markdown this reads. The PDF is gitignored for the same reason CDME_v1_adversarial_findings.pdf
is -- a generated artifact that would otherwise churn in every diff.

    python3 evidence/blind_pass/render_findings_pdf.py CDME_v2_audit_findings.pdf

Run it from the REPOSITORY ROOT: every source path below is root-relative, and running it from
this directory silently produces a PDF containing only the title page.

Part I is the mandate, Part II the consolidated record and the reproducibility mandate, Part III
the thirteen verbatim pass reports. Part III is regenerated from a glob, so a report added to
reports_v2/ appears without editing this file.
"""
import re, sys, html, pathlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether, HRFlowable, Preformatted)

INK   = colors.HexColor("#161514")
MUTED = colors.HexColor("#6b6660")
RULE  = colors.HexColor("#cfc8be")
BAND  = colors.HexColor("#f2eee7")
ACC   = colors.HexColor("#7a3418")

def st(name, **kw):
    base = dict(fontName="Times-Roman", fontSize=9.6, leading=13.2, textColor=INK,
                spaceAfter=6, allowWidows=0, allowOrphans=0)
    base.update(kw); return ParagraphStyle(name, **base)

S = {
 "h1": st("h1", fontName="Helvetica-Bold", fontSize=17, leading=20, textColor=ACC,
          spaceBefore=18, spaceAfter=9),
 "h2": st("h2", fontName="Helvetica-Bold", fontSize=11.6, leading=14.5, spaceBefore=13, spaceAfter=5),
 "h3": st("h3", fontName="Helvetica-Bold", fontSize=10.2, leading=13, spaceBefore=9, spaceAfter=4),
 "p":  st("p"),
 "li": st("li", leftIndent=13, bulletIndent=3, spaceAfter=3.5),
 "cell": st("cell", fontSize=7.9, leading=10.0, spaceAfter=0),
 "cellh": st("cellh", fontName="Helvetica-Bold", fontSize=7.9, leading=10.0, spaceAfter=0),
 "title": st("title", fontName="Helvetica-Bold", fontSize=25, leading=29, textColor=ACC, spaceAfter=10),
 "sub": st("sub", fontSize=11, leading=15, textColor=MUTED, spaceAfter=4),
}

def inline(t):
    """markdown inline -> reportlab markup"""
    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c == "`":
            j = t.find("`", i+1)
            if j == -1: out.append(html.escape(c)); i += 1; continue
            out.append('<font face="Courier" size="8.4">%s</font>' % html.escape(t[i+1:j]))
            i = j+1
        elif t.startswith("**", i):
            j = t.find("**", i+2)
            if j == -1: out.append("**"); i += 2; continue
            out.append("<b>%s</b>" % inline(t[i+2:j])); i = j+2
        elif c == "*":
            j = t.find("*", i+1)
            if j == -1: out.append("*"); i += 1; continue
            out.append("<i>%s</i>" % inline(t[i+1:j])); i = j+1
        else:
            out.append(html.escape(c)); i += 1
    return "".join(out)

def render(md, flow, avail):
    lines = md.split("\n")
    i, n = 0, len(lines)
    buf = []
    def flush():
        if buf:
            flow.append(Paragraph(inline(" ".join(buf).strip()), S["p"])); buf.clear()
    while i < n:
        L = lines[i]
        s = L.rstrip()
        if s.startswith("```"):
            flush(); i += 1; code = []
            while i < n and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            flow.append(Table([[Preformatted("\n".join(code), st("code", fontName="Courier",
                        fontSize=7.4, leading=9.4, spaceAfter=0))]],
                        colWidths=[avail], style=TableStyle([
                            ("BACKGROUND",(0,0),(-1,-1),BAND), ("BOX",(0,0),(-1,-1),0.4,RULE),
                            ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
                            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)])))
            flow.append(Spacer(1, 7)); continue
        if re.match(r"^\s*\|", s) and i+1 < n and re.match(r"^\s*\|[\s:|-]+\|?\s*$", lines[i+1]):
            flush()
            rows = []
            while i < n and re.match(r"^\s*\|", lines[i]):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[\s:|-]+$", "".join(cells)): rows.append(cells)
                i += 1
            w = max(len(r) for r in rows)
            rows = [r + [""]*(w-len(r)) for r in rows]
            # width: first column narrower when many columns
            cw = [avail/w]*w
            if w >= 3: cw = [avail*0.12] + [avail*0.88/(w-1)]*(w-1)
            data = [[Paragraph(inline(c), S["cellh" if ri==0 else "cell"]) for c in r]
                    for ri, r in enumerate(rows)]
            t = Table(data, colWidths=cw, repeatRows=1, style=TableStyle([
                ("BACKGROUND",(0,0),(-1,0),BAND),
                ("LINEBELOW",(0,0),(-1,0),0.6,RULE),
                ("INNERGRID",(0,1),(-1,-1),0.25,colors.HexColor("#e4ded4")),
                ("BOX",(0,0),(-1,-1),0.4,RULE),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
                ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
            flow.append(t); flow.append(Spacer(1, 9)); continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush(); lvl = len(m.group(1))
            key = "h1" if lvl == 1 else ("h2" if lvl == 2 else "h3")
            flow.append(Paragraph(inline(m.group(2)), S[key]))
            if lvl == 1: flow.append(HRFlowable(width="100%", thickness=0.7, color=RULE,
                                                spaceBefore=1, spaceAfter=8))
            i += 1; continue
        if re.match(r"^\s*(---|___|\*\*\*)\s*$", s):
            flush(); flow.append(HRFlowable(width="100%", thickness=0.4, color=RULE,
                                            spaceBefore=6, spaceAfter=9)); i += 1; continue
        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", s)
        if m:
            flush()
            ind = len(m.group(1))
            bullet = "•" if m.group(2) in "-*+" else m.group(2)
            body = m.group(3)
            while i+1 < n and lines[i+1].startswith(" "*(ind+2)) and lines[i+1].strip() \
                  and not re.match(r"^\s*([-*+]|\d+\.)\s", lines[i+1]):
                i += 1; body += " " + lines[i].strip()
            style = ParagraphStyle("li%d" % ind, parent=S["li"], leftIndent=13+ind*9,
                                   bulletIndent=3+ind*9)
            flow.append(Paragraph(inline(body), style, bulletText=bullet)); i += 1; continue
        if not s.strip(): flush(); i += 1; continue
        buf.append(s.strip()); i += 1
    flush()

def main(out):
    root = pathlib.Path(".")
    avail = LETTER[0] - 1.5*inch
    flow = []
    flow += [Spacer(1, 1.5*inch),
             Paragraph("The Dynasty Collective", S["sub"]),
             Paragraph("v2 Adversarial Audit &mdash; All Findings", S["title"]),
             HRFlowable(width="45%", thickness=2, color=ACC, spaceAfter=14, hAlign="LEFT"),
             Paragraph("Thirteen blind passes over the frozen v2 engine, consolidated into a "
                       "repair mandate of twenty-six items, six owner decisions and one reopened "
                       "register item. Every finding is mapped; every verbatim report is reproduced.",
                       S["sub"]),
             Spacer(1, 22),
             Paragraph("Frozen candidate <b>a8d1627</b>, tag <b>v2-freeze</b>. Audit conducted after "
                       "the freeze, on branch <font face=\"Courier\" size=\"9\">"
                       "claude/fantasy-football-control-center-ff6qlu</font>.", S["p"]),
             Paragraph("Compiled 2026-09-28.", S["p"]),
             PageBreak()]

    parts = [("PART I — The repair mandate", ["REPAIR_MANDATE_V2.md"]),
             ("PART II — Consolidated findings and protocol record",
              ["evidence/blind_pass/FINDINGS_V2.md", "evidence/blind_pass/MANDATE_V2.md"]),
             ("PART III — The thirteen verbatim pass reports",
              sorted(str(q) for q in root.glob("evidence/blind_pass/reports_v2/*.md")))]
    for title, files in parts:
        flow += [Paragraph(title, S["h1"]),
                 HRFlowable(width="100%", thickness=0.7, color=RULE, spaceAfter=10)]
        for f in files:
            pth = root / f
            if not pth.exists(): continue
            flow.append(Paragraph("<font color='#6b6660'>source:</font> "
                                  "<font face='Courier' size='8'>%s</font>" % html.escape(f),
                                  st("src", fontSize=8, textColor=MUTED, spaceAfter=8)))
            render(pth.read_text(), flow, avail)
            flow.append(PageBreak())

    def deco(canv, doc):
        canv.saveState()
        canv.setFont("Helvetica", 7.2); canv.setFillColor(MUTED)
        canv.drawString(0.75*inch, 0.52*inch, "The Dynasty Collective — v2 adversarial audit")
        canv.drawRightString(LETTER[0]-0.75*inch, 0.52*inch, "%d" % doc.page)
        canv.setStrokeColor(RULE); canv.setLineWidth(0.4)
        canv.line(0.75*inch, 0.68*inch, LETTER[0]-0.75*inch, 0.68*inch)
        canv.restoreState()

    SimpleDocTemplate(out, pagesize=LETTER, topMargin=0.8*inch, bottomMargin=0.85*inch,
                      leftMargin=0.75*inch, rightMargin=0.75*inch,
                      title="v2 Adversarial Audit — All Findings",
                      author="The Dynasty Collective").build(flow, onFirstPage=deco,
                                                             onLaterPages=deco)
    print("wrote", out)

main(sys.argv[1] if len(sys.argv) > 1 else "CDME_v2_audit_findings.pdf")
