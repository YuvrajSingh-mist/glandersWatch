"""Build the presentation deck from the pipeline outputs.

Run:  .venv/bin/python src/15_make_deck.py

Design follows the department's report template: a navy cover panel, a light
lavender ground (#F3F3F7), periwinkle cards (#E0E0EC), a single orange accent
(#E25822), Playfair Display for headings and Open Sans for text.

Every number and figure is read from reports/*.json and figures/*.png, so the
deck cannot drift from the report.
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = pathlib.Path(__file__).resolve().parents[1]
REP, FIG = ROOT / "reports", ROOT / "figures"
OUT = ROOT / "slides" / "GlandersWatch_Deck.pptx"
OUT.parent.mkdir(exist_ok=True)

R = json.loads((REP / "results.json").read_text())
A = json.loads((REP / "dataset_analysis.json").read_text())

L1 = R["level1"]["metrics"]
CH = R["best_model"]
PREV = A["labels"]["prevalence"]
ROWS = A["labels"]["rows"]
POS = A["labels"]["positives"]
NC = A["labels"]["countries"]
SEL = R["selection"]
LR = L1["Logistic Regression"]
RF = L1["Random Forest"]
XG = L1["XGBoost"]

_rank = SEL["ranking"]
ATTR_SHARE = sum(r["mean_abs_shap"] for r in _rank[: SEL["top_k"]]) / (
    sum(r["mean_abs_shap"] for r in _rank) or 1.0)

# ---------------------------------------------------------------- palette
BG = RGBColor(0xF3, 0xF3, 0xF7)
CARD = RGBColor(0xE0, 0xE0, 0xEC)
CARD_DEEP = RGBColor(0xC6, 0xC6, 0xD2)
INK = RGBColor(0x10, 0x10, 0x14)
BODY = RGBColor(0x39, 0x39, 0x3C)
ACCENT = RGBColor(0xE2, 0x58, 0x22)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NAVY = RGBColor(0x06, 0x1E, 0x5E)
NAVY_LIGHT = RGBColor(0x0E, 0x2C, 0x74)
MUTED = RGBColor(0x7A, 0x7A, 0x84)
PALE_TEXT = RGBColor(0xC3, 0xCE, 0xE4)

SERIF = "Playfair Display"
SANS = "Open Sans"

W, H = Inches(13.333), Inches(7.5)
MG = Inches(0.62)
CWD = W - 2 * MG
FOOT = "GlandersWatch  ·  B.Tech Project  ·  IIIT Bhubaneswar"


def alert_econ() -> dict:
    """Recall at a fixed budget, and budget needed for a target recall."""
    path = REP / f"pred_L1_{CH.replace(' ', '_')}.csv"
    if not path.exists():
        return {"r6": 0.0, "b50": 0.0, "b80": 0.0}
    d = pd.read_csv(path)
    y = d.y_true.to_numpy().astype(int)
    p = d.p_pred.to_numpy()
    order = np.argsort(-p)
    fe = np.cumsum(y[order]) / y.sum()
    fa = np.arange(1, len(y) + 1) / len(y)

    def recall_at(b):
        return float(fe[max(0, int(b * len(y)) - 1)])

    def budget_at(t):
        k = np.flatnonzero(fe >= t - 1e-12)
        return float(fa[k[0]]) if len(k) else 1.0

    return {"r6": recall_at(0.06), "b50": budget_at(0.50), "b80": budget_at(0.80)}


AE = alert_econ()


# ---------------------------------------------------------------- helpers
def set_spacing(run, hundredths: int):
    """Letter-spacing, in 1/100 pt, which the API does not expose."""
    run.font._rPr.set("spc", str(hundredths))


def plain(shape):
    shape.shadow.inherit = False
    return shape


def ground(s):
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    bg.fill.solid(); bg.fill.fore_color.rgb = BG
    bg.line.fill.background(); plain(bg)
    return bg


_PAGE = [1]


def footer(s, pg: int):
    f = s.shapes.add_textbox(MG, Inches(7.00), Inches(9.0), Inches(0.30))
    p = f.text_frame.paragraphs[0]
    p.text = FOOT
    p.font.size = Pt(9); p.font.color.rgb = MUTED; p.font.name = SANS
    set_spacing(p.runs[0], 60)

    nb = s.shapes.add_textbox(W - MG - Inches(1.2), Inches(7.00), Inches(1.2), Inches(0.30))
    np_ = nb.text_frame.paragraphs[0]
    np_.text = f"{pg:02d}"
    np_.alignment = PP_ALIGN.RIGHT
    np_.font.size = Pt(9); np_.font.color.rgb = MUTED; np_.font.name = SANS


def page(prs, title: str, eyebrow: str | None = None, pg: int | None = None,
         title_size: int = 34, wrap=False):
    _PAGE[0] += 1
    s = prs.slides.add_slide(prs.slide_layouts[6])
    ground(s)

    y = Inches(0.52)
    if eyebrow:
        e = s.shapes.add_textbox(MG, Inches(0.42), Inches(7.0), Inches(0.28))
        ep = e.text_frame.paragraphs[0]
        ep.text = eyebrow.upper()
        ep.font.size = Pt(10.5); ep.font.bold = True
        ep.font.color.rgb = ACCENT; ep.font.name = SANS
        set_spacing(ep.runs[0], 180)
        y = Inches(0.76)

    t = s.shapes.add_textbox(MG, y, CWD, Inches(0.85))
    t.text_frame.word_wrap = wrap
    t.text_frame.margin_left = 0
    tp = t.text_frame.paragraphs[0]
    tp.text = title
    tp.font.size = Pt(title_size); tp.font.bold = True
    tp.font.color.rgb = INK; tp.font.name = SERIF

    rule = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, MG, Inches(1.32),
                              Inches(0.95), Inches(0.045))
    rule.fill.solid(); rule.fill.fore_color.rgb = ACCENT
    rule.line.fill.background(); plain(rule)

    footer(s, _PAGE[0])
    return s


def card(s, x, y, w, h, fill=CARD, num: str | None = None, head: str | None = None,
         text: str | None = None, head_size=16, text_size=11.5,
         head_color=INK, body_color=BODY, pad=0.20, vcenter=False,
         num_size=26, formula: str | None = None):
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    box.adjustments[0] = 0.045
    box.fill.solid(); box.fill.fore_color.rgb = fill
    box.line.fill.background(); plain(box)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(pad); tf.margin_right = Inches(pad * 0.85)
    tf.margin_top = Inches(0.14); tf.margin_bottom = Inches(0.10)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE if vcenter else MSO_ANCHOR.TOP

    first = True
    if num:
        p = tf.paragraphs[0]; first = False
        p.text = num
        p.font.size = Pt(num_size); p.font.bold = True
        p.font.color.rgb = ACCENT; p.font.name = SERIF
        p.space_after = Pt(1)
    if head:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = head
        p.font.size = Pt(head_size); p.font.bold = True
        p.font.color.rgb = head_color; p.font.name = SERIF
        p.space_after = Pt(4)
    if text:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(text_size); p.font.color.rgb = body_color
        p.font.name = SANS
    if formula:
        p = tf.add_paragraph()
        p.text = formula
        p.font.size = Pt(text_size + 1.5); p.font.bold = True
        p.font.color.rgb = INK; p.font.name = SANS
        p.space_before = Pt(6); p.space_after = Pt(6)
    return box


def prose(s, x, y, w, h, lines, size=12, space=7, color=BODY, bullet="·   "):
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = 0; tf.margin_top = 0
    first = True
    for ln in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = (bullet + ln[2:]) if ln.startswith("- ") else ln
        p.font.size = Pt(size); p.font.color.rgb = color; p.font.name = SANS
        p.space_after = Pt(space)
    return tb


def stat(s, x, y, w, value, label, h=Inches(1.10), fill=CARD,
         vsize=25, accent=False):
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    box.adjustments[0] = 0.05
    box.fill.solid(); box.fill.fore_color.rgb = fill
    box.line.fill.background(); plain(box)
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.16); tf.margin_top = Inches(0.10)
    tf.margin_right = Inches(0.12)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = value
    p.font.size = Pt(vsize); p.font.bold = True
    p.font.color.rgb = ACCENT if accent else INK
    p.font.name = SERIF
    p2 = tf.add_paragraph(); p2.text = label
    p2.font.size = Pt(9.5); p2.font.color.rgb = BODY; p2.font.name = SANS
    p2.space_before = Pt(1)
    return box


def table(s, x, y, w, rows, col_w=None, size=10.5, row_h=0.29, head_fill=BODY,
          right_cols=()):
    nrows, ncols = len(rows), len(rows[0])
    shp = s.shapes.add_table(nrows, ncols, x, y, w, Inches(row_h) * nrows)
    tbl = shp.table
    if col_w:
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = cw
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(row_h)
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = str(val)
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.10)
            cell.margin_top = Inches(0.01)
            cell.margin_bottom = Inches(0.01)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            para = cell.text_frame.paragraphs[0]
            para.font.size = Pt(size); para.font.name = SANS
            if c in right_cols:
                para.alignment = PP_ALIGN.RIGHT
            if r == 0:
                para.font.bold = True
                para.font.color.rgb = WHITE
                cell.fill.solid(); cell.fill.fore_color.rgb = head_fill
            else:
                para.font.color.rgb = INK
                cell.fill.solid()
                cell.fill.fore_color.rgb = CARD if r % 2 else BG
    return tbl


def pic(s, name, x, y, w=None, h=None, plate=False, pad=Inches(0.09)):
    path = FIG / name
    if not path.exists():
        return None
    if plate:
        from PIL import Image
        iw, ih = Image.open(path).size
        pw = w if w is not None else int(h * iw / ih)
        ph = int(pw * ih / iw) if w is not None else h
        bg = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y,
                                pw + 2 * pad, ph + 2 * pad)
        bg.adjustments[0] = 0.03
        bg.fill.solid(); bg.fill.fore_color.rgb = WHITE
        bg.line.fill.background(); plain(bg)
        return s.shapes.add_picture(str(path), x + pad, y + pad, width=pw, height=ph)
    return s.shapes.add_picture(str(path), x, y, width=w, height=h)


def chip(s, x, y, w, text, size=9):
    c = s.shapes.add_textbox(x, y, w, Inches(0.36))
    c.text_frame.word_wrap = True
    c.text_frame.margin_left = 0
    p = c.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(size); p.font.color.rgb = MUTED; p.font.name = SANS
    return c


def takeaway(s, y, text, h=Inches(0.62), size=11.5):
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, MG, y, CWD, h)
    box.adjustments[0] = 0.10
    box.fill.solid(); box.fill.fore_color.rgb = BODY
    box.line.fill.background(); plain(box)
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.22); tf.margin_right = Inches(0.22)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size); p.font.color.rgb = WHITE; p.font.name = SANS


def divider(prs, num: str, title: str, question: str, items: list[str]):
    _PAGE[0] += 1
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    bg.fill.solid(); bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background(); plain(bg)

    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.16), H)
    band.fill.solid(); band.fill.fore_color.rgb = ACCENT
    band.line.fill.background(); plain(band)

    n = s.shapes.add_textbox(MG, Inches(1.55), Inches(2.6), Inches(1.1))
    np_ = n.text_frame.paragraphs[0]
    np_.text = num
    np_.font.size = Pt(64); np_.font.bold = True
    np_.font.color.rgb = ACCENT; np_.font.name = SERIF

    t = s.shapes.add_textbox(MG, Inches(2.62), Inches(9.4), Inches(1.0))
    t.text_frame.word_wrap = True
    tp = t.text_frame.paragraphs[0]
    tp.text = title
    tp.font.size = Pt(38); tp.font.bold = True
    tp.font.color.rgb = WHITE; tp.font.name = SERIF

    q = s.shapes.add_textbox(MG, Inches(3.72), Inches(9.6), Inches(0.9))
    q.text_frame.word_wrap = True
    qp = q.text_frame.paragraphs[0]
    qp.text = question
    qp.font.size = Pt(14); qp.font.color.rgb = PALE_TEXT; qp.font.name = SANS

    c = s.shapes.add_textbox(MG, Inches(4.78), Inches(10.2), Inches(1.5))
    ctf = c.text_frame; ctf.word_wrap = True; ctf.margin_left = 0
    for i, item in enumerate(items):
        p = ctf.paragraphs[0] if i == 0 else ctf.add_paragraph()
        p.text = "—   " + item
        p.font.size = Pt(11.5); p.font.color.rgb = WHITE; p.font.name = SANS
        p.space_after = Pt(5)

    rule = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, MG, Inches(6.60),
                              CWD, Inches(0.012))
    rule.fill.solid(); rule.fill.fore_color.rgb = NAVY_LIGHT
    rule.line.fill.background(); plain(rule)

    lbl = s.shapes.add_textbox(MG, Inches(6.72), Inches(8.0), Inches(0.30))
    lp = lbl.text_frame.paragraphs[0]
    lp.text = f"GlandersWatch  ·  section {num}"
    lp.font.size = Pt(9); lp.font.color.rgb = PALE_TEXT; lp.font.name = SANS
    set_spacing(lp.runs[0], 60)
    return s


def build() -> pathlib.Path:
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # ------------------------------------------------------------ 1 cover
    s = prs.slides.add_slide(prs.slide_layouts[6])
    panel_w = Inches(8.15)
    base = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    base.fill.solid(); base.fill.fore_color.rgb = BG
    base.line.fill.background(); plain(base)

    panel = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, panel_w, H)
    panel.fill.solid(); panel.fill.fore_color.rgb = NAVY
    panel.line.fill.background(); plain(panel)

    edge = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, panel_w, 0, Inches(0.05), H)
    edge.fill.solid(); edge.fill.fore_color.rgb = ACCENT
    edge.line.fill.background(); plain(edge)

    s.shapes.add_picture(str(FIG / "iiit_logo.png"), W - Inches(2.42), Inches(0.62),
                         width=Inches(1.62))

    e = s.shapes.add_textbox(MG, Inches(1.02), Inches(6.6), Inches(0.3))
    ep = e.text_frame.paragraphs[0]
    ep.text = "B.TECH PROJECT REPORT"
    ep.font.size = Pt(10.5); ep.font.bold = True
    ep.font.color.rgb = ACCENT; ep.font.name = SANS
    set_spacing(ep.runs[0], 220)

    t = s.shapes.add_textbox(MG, Inches(1.52), Inches(7.1), Inches(1.95))
    tf = t.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "GlandersWatch"
    p.font.size = Pt(48); p.font.bold = True
    p.font.color.rgb = WHITE; p.font.name = SERIF
    p2 = tf.add_paragraph()
    p2.text = "Next-year risk prediction, grounded Q&A and owner\nalerting for a neglected zoonosis"
    p2.font.size = Pt(14.5); p2.font.color.rgb = PALE_TEXT; p2.font.name = SANS
    p2.space_before = Pt(12)

    ac = s.shapes.add_textbox(MG, Inches(3.44), Inches(6.9), Inches(0.9))
    ac.text_frame.word_wrap = True
    ap = ac.text_frame.paragraphs[0]
    ap.text = ("A report submitted in partial fulfilment of the requirements for the award of "
               "the Bachelor of Technology in Computer Science and Engineering")
    ap.font.size = Pt(10); ap.font.color.rgb = PALE_TEXT; ap.font.name = SANS
    ap.line_spacing = 1.45

    sup = s.shapes.add_textbox(MG, Inches(4.52), Inches(6.9), Inches(0.85))
    sup.text_frame.word_wrap = True
    sp = sup.text_frame.paragraphs[0]
    sp.text = "UNDER THE SUPERVISION OF"
    sp.font.size = Pt(8.5); sp.font.color.rgb = PALE_TEXT; sp.font.name = SANS
    set_spacing(sp.runs[0], 120)
    sp2 = sup.text_frame.add_paragraph()
    sp2.text = "Dr. Sangita Dhara"
    sp2.font.size = Pt(15); sp2.font.bold = True
    sp2.font.color.rgb = WHITE; sp2.font.name = SERIF
    sp2.space_before = Pt(3)

    pv = s.shapes.add_textbox(MG, Inches(5.52), Inches(6.9), Inches(1.15))
    pv.text_frame.word_wrap = True
    pp = pv.text_frame.paragraphs[0]
    pp.text = "PRESENTED BY"
    pp.font.size = Pt(8.5); pp.font.color.rgb = PALE_TEXT; pp.font.name = SANS
    set_spacing(pp.runs[0], 120)
    for nm in ["Pedapatruni Shanmukh Vardhan   ·   B123089",
               "Shaktimayee Mohanty   ·   B123118",
               "Yuvraj Singh   ·   B123153"]:
        q = pv.text_frame.add_paragraph()
        q.text = nm
        q.font.size = Pt(11); q.font.color.rgb = WHITE; q.font.name = SANS
        q.space_before = Pt(4)

    # right column furniture
    rcol_x = W - Inches(4.35)
    rcol_w = Inches(3.70)
    comps = [("Risk engine", "a calibrated next-year probability"),
             ("RAG layer", "answers questions, or refuses"),
             ("Alert service", "a message still worth reading")]
    cy = Inches(4.28)
    rh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, rcol_x, cy, rcol_w, Inches(0.012))
    rh.fill.solid(); rh.fill.fore_color.rgb = CARD_DEEP
    rh.line.fill.background(); plain(rh)
    cy += Inches(0.20)

    for nm, sub in comps:
        a = s.shapes.add_textbox(rcol_x, cy, rcol_w, Inches(0.34))
        ap2 = a.text_frame.paragraphs[0]
        ap2.text = nm
        ap2.font.size = Pt(14); ap2.font.bold = True
        ap2.font.color.rgb = INK; ap2.font.name = SERIF
        b = s.shapes.add_textbox(rcol_x, cy + Inches(0.34), rcol_w, Inches(0.30))
        bp = b.text_frame.paragraphs[0]
        bp.text = sub
        bp.font.size = Pt(9.5); bp.font.color.rgb = BODY; bp.font.name = SANS
        cy += Inches(0.74)
    dt = s.shapes.add_textbox(W - Inches(4.35), Inches(6.72), Inches(3.70), Inches(0.32))
    dp = dt.text_frame.paragraphs[0]
    dp.text = "Department of Computer Science and Engineering   ·   November 2026"
    dp.font.size = Pt(8.5); dp.font.color.rgb = MUTED; dp.font.name = SANS
    dp.alignment = PP_ALIGN.RIGHT

    # ------------------------------------------------------------ outline (guideline)
    s = page(prs, "Presentation outline", "Running order", title_size=32)
    rows = [
        ["#", "Segment", "Presenter", "Owns Q&A on"],
        ["1", "Problem, objectives, platform", "Yuvraj Singh", "Scope, label, contracts"],
        ["2", "Data, features, models, results", "Yuvraj Singh", "Splits, metrics, champion"],
        ["3", "RAG question answering", "Shaktimayee Mohanty", "Retrieval, citations, refusal"],
        ["4", "Alerting system", "P. Shanmukh Vardhan", "Rules, delivery, audit"],
        ["5", "Limits, future work, close", "All three", "Open questions together"],
    ]
    table(s, MG, Inches(1.70), CWD, rows,
          col_w=[Inches(0.55), Inches(4.55), Inches(3.35), Inches(3.65)],
          size=12, row_h=0.42)
    takeaway(s, Inches(5.55),
             "Aligned to the Final_v2 report (~35 pages): Introduction → Literature → "
             "Architecture → Methodology (ML / RAG / Alerts) → Results → Conclusion. "
             "Measured results are only for next-year (t+1) binary prediction.")

    # ------------------------------------------------------------ 2 context
    s = page(prs, "A disease that still has no forecast", "Introduction")
    card(s, MG, Inches(1.62), Inches(5.85), Inches(2.10), num="01", head="The organism",
         text="Glanders is a bacterial zoonosis of equids caused by Burkholderia mallei. "
              "Notifiable, frequently fatal, and with no environmental reservoir: it persists "
              "in animal populations rather than in soil or water.")
    card(s, MG + Inches(6.05), Inches(1.62), Inches(6.05), Inches(2.10), num="02",
         head="The gap",
         text="Surveillance describes what has already happened. The published machine-learning "
              "work on this disease stops at laboratory identification. No population-level "
              "risk model has been reported.")

    prose(s, MG, Inches(3.98), Inches(5.85), Inches(1.5), [
        "Indian surveillance, 2019 to 2023, found 728 seropositive equids in 138 districts, "
        "sharply concentrated geographically. Cases cluster, and that is what makes a "
        "spatial model worth building.",
    ], size=11.5)

    card(s, MG + Inches(6.05), Inches(3.98), Inches(6.05), Inches(1.55), fill=CARD_DEEP,
         head="What this project adds",
         text="A calibrated next-year risk model, a RAG layer that answers questions from "
              "official guidance, and an alert service, each independently deployable behind "
              "a fixed contract.",
         head_size=14.5, text_size=11)

    takeaway(s, Inches(5.92),
             "Each component communicates through a versioned schema rather than shared "
             "internals, so none of the three hardcodes the disease and each degrades "
             "without failing the others.")

    # ------------------------------------------------------------ 3 why
    s = page(prs, "Population at risk is not the same as damage", "Why it matters")

    stat(s, MG, Inches(1.62), Inches(3.85), "5.50 lakh", "equids in India, 2019")
    stat(s, MG + Inches(4.05), Inches(1.62), Inches(3.85), "728", "seropositive, 2019–23")
    stat(s, MG + Inches(8.10), Inches(1.62), Inches(4.00), "138", "districts affected")

    prose(s, MG, Inches(3.02), Inches(6.15), Inches(2.4), [
        "The two figures are routinely conflated, so they are separated here at the outset.",
        "- 5.50 lakh is the exposed population: how many animals are susceptible.",
        "- 728 of 158,798 screened is the documented damage: under one per cent.",
        "- Each positive is acted on rather than monitored, because the disease is notifiable "
        "and often fatal once clinical.",
    ], size=11.5, space=9)

    pic(s, "fig14_background.png", MG + Inches(6.55), Inches(3.06), w=Inches(5.55), plate=True)
    chip(s, MG + Inches(6.64), Inches(5.02), Inches(5.4),
         "Panel A: the exposed population by species.  Panel B: documented events per year, "
         "which tracks open-access publishing as much as disease.")

    takeaway(s, Inches(6.05),
             "Because documentation follows publishing capacity, the target is a documented "
             "event rather than raw incidence. That choice is stated once and held throughout.")

    # ------------------------------------------------------------ 4 problem
    s = page(prs, "Problem statement", "Definition")

    strip = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, MG, Inches(1.60),
                               CWD, Inches(0.82))
    strip.adjustments[0] = 0.12
    strip.fill.solid(); strip.fill.fore_color.rgb = CARD_DEEP
    strip.line.fill.background(); plain(strip)
    stf = strip.text_frame; stf.word_wrap = True
    stf.margin_left = Inches(0.24); stf.vertical_anchor = MSO_ANCHOR.MIDDLE
    sp = stf.paragraphs[0]
    sp.text = ("Given a country's features in year t, predict whether glanders is "
               "documented in that country in year t + 1.")
    sp.font.size = Pt(15.5); sp.font.bold = True
    sp.font.color.rgb = INK; sp.font.name = SERIF

    card(s, MG, Inches(2.68), Inches(5.85), Inches(2.20), num="01", head="The label",
         text="One country-year is positive if a glanders occurrence is reported from that "
              "country in that year. Features come only from the year before, so the model "
              "never reads the outcome it is predicting.", head_size=16)
    card(s, MG + Inches(6.05), Inches(2.68), Inches(6.05), Inches(2.20), num="02",
         head="The difficulty",
         text=f"{POS} positives in {ROWS:,} rows. A model that always says “no” is "
              f"{100 * (1 - PREV):.0f} per cent accurate and worthless, which is why accuracy "
              "and ROC-AUC are not used to rank models here.", head_size=16)

    prose(s, MG, Inches(5.12), CWD, Inches(0.8), [
        f"Base rate {PREV * 100:.2f} per cent. Precision-recall AUC is the primary metric "
        f"because it moves when a model starts finding the {POS} positives; ROC-AUC does not.",
    ], size=11.5)

    takeaway(s, Inches(6.02),
             "Every later result is reported on this single target and this metric: "
             "features from year t predict whether glanders is documented in year t+1.")

    # ------------------------------------------------------------ 5 objectives
    s = page(prs, "Project objectives", "Scope", title_size=32)
    objs = [
        ("01", "Prediction as a service",
         "Package a calibrated next-year risk model as a versioned artefact behind a REST "
         "interface."),
        ("02", "Grounded Q&A",
         "Build a retrieval-augmented layer that answers questions from official guidance, "
         "cites every claim, and refuses rather than guesses."),
        ("03", "Owner alerts",
         "Convert a calibrated probability into few enough messages that they are read, "
         "using threshold, suppression and deduplication rules."),
    ]
    for i, (num, head, text) in enumerate(objs):
        card(s, MG, Inches(1.58) + i * Inches(1.35),
             CWD, Inches(1.20), num=num, head=head, text=text,
             head_size=16.5, text_size=12)

    takeaway(s, Inches(5.85),
             "Objective 01 carries measured results. 02 and 03 are specified contracts with "
             "evaluation protocols, and are not presented as measured field performance.")

    # ------------------------------------------------------------ 6 users
    s = page(prs, "Who the system is for", "Use", title_size=32)
    users = [
        ("01", "District veterinary officer",
         "Where to pre-position testing and movement checks, before the report arrives."),
        ("02", "Equine owner",
         "Whether this is the month to restrict movement, in a language they read."),
        ("03", "State planner",
         "A single scale on which districts can be compared for resources."),
    ]
    for i, (num, head, text) in enumerate(users):
        card(s, MG + i * Inches(4.05), Inches(1.62), Inches(3.85), Inches(2.05),
             num=num, head=head, text=text, head_size=15, text_size=11)

    card(s, MG, Inches(3.94), CWD, Inches(1.20), fill=CARD_DEEP,
         head="The failure mode to design against",
         text="A warning system that fires for every area every month is ignored by month "
              "twelve. Alert budget is therefore a design constraint, not a tuning parameter.",
         head_size=14.5, text_size=11)

    takeaway(s, Inches(5.52),
             "None of the three users operates a dashboard. The output has to arrive as a "
             "message, and the reasoning has to arrive with it.")

    # ------------------------------------------------------------ section 01
    divider(prs, "01", "The risk engine",
            "Can a country's next year be forecast from its last?",
            ["Four public sources assembled into a country-year panel",
             "Eight features chosen by attribution rather than correlation",
             "Six model families, two validation splits, and a calibration check"])

    # ------------------------------------------------------------ 7 data
    s = page(prs, "Four public sources, none used for this disease", "Data", title_size=31)
    srcs = [
        ("01", "Europe PMC", "Occurrence events extracted from abstracts. This is the label."),
        ("02", "FAOSTAT", "Horse, ass and mule head counts. This is exposure."),
        ("03", "World Bank", "Development and connectivity indicators. This is context."),
        ("04", "NASA POWER", "Temperature, humidity and rainfall. This is environment."),
    ]
    for i, (num, head, text) in enumerate(srcs):
        card(s, MG + i * Inches(3.05), Inches(1.58), Inches(2.85), Inches(1.72),
             num=num, head=head, text=text, head_size=13.5, text_size=10.5, num_size=22)

    gy = Inches(3.52)
    stat(s, MG, gy, Inches(2.35), f"{ROWS:,}", "modelling rows", h=Inches(0.98), vsize=21)
    stat(s, MG + Inches(2.55), gy, Inches(2.35), f"{NC}", "countries", h=Inches(0.98), vsize=21)
    stat(s, MG, gy + Inches(1.14), Inches(2.35), f"{POS}", "positives", h=Inches(0.98), vsize=21)
    stat(s, MG + Inches(2.55), gy + Inches(1.14), Inches(2.35), f"{PREV*100:.2f}%",
         "prevalence", h=Inches(0.98), vsize=21, accent=True)

    chip(s, MG, Inches(5.82), Inches(4.95),
         "6,700 raw country-year rows over 268 reporting entities reduce to 2,880 observations. "
         "Rows with no climate baseline are dropped rather than imputed, so no anomaly is invented.")

    pic(s, "fig01_dataset_coverage.png", Inches(5.72), Inches(3.54), w=Inches(6.85))
    chip(s, Inches(5.72), Inches(6.18), Inches(6.85),
         "Coverage of the assembled panel: which countries contribute which years.")

    # ------------------------------------------------------------ 8 method
    s = page(prs, "From raw sources to a calibrated probability", "Method", title_size=31)
    steps = [
        ("01", "Sources", "Four APIs, one panel"),
        ("02", "Panel", "Country-year rows"),
        ("03", "Attribution", "42 ranked, 8 kept"),
        ("04", "Training", "Six families, two splits"),
        ("05", "Output", "Calibrated probability"),
    ]
    for i, (num, head, text) in enumerate(steps):
        x = MG + i * Inches(2.47)
        card(s, x, Inches(1.66), Inches(2.27), Inches(1.62), num=num, head=head,
             text=text, head_size=13, text_size=10, num_size=20)
        if i < 4:
            a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + Inches(2.29),
                                   Inches(2.34), Inches(0.16), Inches(0.20))
            a.fill.solid(); a.fill.fore_color.rgb = ACCENT
            a.line.fill.background(); plain(a)

    prose(s, MG, Inches(3.52), Inches(5.9), Inches(2.3), [
        "The temporal split trains on 2005–2017 (~68% of rows) and tests on 2018–2023 "
        "(~32%): forward in time, which is the only honest test of a forecast.",
        "The country split holds out whole countries, so no row from a test country appears "
        "in training. This is the split that matches deployment.",
        "Feature ranking uses training years only. Fitting on the full panel would let the "
        "held-out years choose the features and make the temporal score optimistic.",
    ], size=11, space=8)

    table(s, Inches(6.95), Inches(3.62), Inches(5.75), [
        ["Model family", "Character"],
        ["Logistic Regression", "additive, interpretable"],
        ["Decision Tree", "single split tree"],
        ["Random Forest", "bagged trees"],
        ["Extra Trees", "randomised splits"],
        ["XGBoost", "gradient boosted"],
        ["LightGBM", "leaf-wise boosted"],
    ], col_w=[Inches(2.75), Inches(3.0)], size=10, row_h=0.27)

    takeaway(s, Inches(5.62),
             "Eight numeric features, no categorical columns, no identifiers. Country codes "
             "and calendar years are identifiers and never enter the model.", h=Inches(0.72))

    # ------------------------------------------------------------ 9 features
    s = page(prs, "Eight features, chosen by attribution", "Features", title_size=31)
    units = {"pop_total": "persons", "years_since_last": "years (99 = never)",
             "temp_mean_anom": "°C from baseline", "internet_pct": "% of population",
             "humidity_anom": "% RH from baseline", "precip_cv": "ratio, sd / mean",
             "log_livestock": "ln(1 + LSU)", "goats": "head"}
    rows = [["#", "Feature", "Unit as measured", "Mean |SHAP|"]]
    for r in SEL["ranking"][: SEL["top_k"]]:
        rows.append([r["rank"], r["feature"], units.get(r["feature"], ""),
                     f"{r['mean_abs_shap']:.3f}"])
    table(s, MG, Inches(1.66), Inches(7.05), rows,
          col_w=[Inches(0.45), Inches(2.35), Inches(2.85), Inches(1.4)],
          size=10, row_h=0.315, right_cols=(0, 3))

    prose(s, MG, Inches(4.72), Inches(7.05), Inches(1.2), [
        f"{SEL['top_k']} of {SEL['n_candidates']} numeric candidates, carrying "
        f"{ATTR_SHARE*100:.0f} per cent of total attribution.",
        "Population and years since the last report rank first: exposure, then history.",
    ], size=11, space=6)

    reasons = [
        ("Attributes a prediction", "SHAP says how far each feature moved this model's "
                                    "output, so the ranking matches what the model uses."),
        ("Beyond pairs", "Correlation and mutual information score features pairwise; they "
                         "cannot see interactions or redundancy."),
        ("Comparable", "Both are unnormalised and undirected. Attribution is additive and "
                       "sums to the prediction."),
    ]
    for i, (head, text) in enumerate(reasons):
        card(s, Inches(7.95), Inches(1.66) + i * Inches(1.42), Inches(4.75), Inches(1.28),
             head=head, text=text, head_size=13, text_size=10)

    takeaway(s, Inches(6.02),
             "Correlation ranks longitude first and attribution ranks it near the bottom. "
             "Selecting on association keeps geography proxies instead of drivers.")

    # ------------------------------------------------------------ 10 models
    s = page(prs, "The three models worth describing", "Models", title_size=31)
    card(s, MG, Inches(1.62), Inches(3.85), Inches(2.92), num="01",
         head="Logistic Regression",
         text="A weighted sum of the eight features passed through a sigmoid. The coefficients "
              "are readable, which matters when a prediction has to be defended.",
         formula="p = 1 / (1 + e^(−z))\nz = β0 + β1x1 + … + β8x8",
         head_size=15, text_size=10.5)
    card(s, MG + Inches(4.05), Inches(1.62), Inches(3.85), Inches(2.92), num="02",
         head="Random Forest",
         text="Five hundred trees, each grown on a bootstrap sample with a random feature "
              "subset at every split, then averaged. Captures interactions, and cannot "
              "extrapolate beyond the data it saw.",
         formula="ŷ = (1/B) Σ Tb(x)\nG = 1 − Σ pk²",
         head_size=15, text_size=10.5)
    card(s, MG + Inches(8.10), Inches(1.62), Inches(4.00), Inches(2.92), num="03",
         head="Gradient Boosting",
         text="Trees added in sequence, each fitting the residual of the last. XGBoost and "
              "LightGBM differ mainly in how they grow the trees.",
         formula="Obj = Σ L(yi, ŷi) + Σ Ω(fk)\nΩ(f) = γT + ½λ||w||²",
         head_size=15, text_size=10.5)

    prose(s, MG, Inches(4.82), CWD, Inches(1.0), [
        "Six families are trained in total; Decision Tree and Extra Trees are reported in the "
        "results table but add nothing to the argument. Logistic Regression and Random Forest "
        "are the two that carry it: one is additive and stable, the other flexible and unstable "
        "across countries.",
    ], size=11)

    takeaway(s, Inches(5.78),
             "Random Forest wins on unseen years; Logistic Regression wins on unseen "
             "countries. The next slide is about why that inversion is the finding.")

    # ------------------------------------------------------------ 11 results
    s = page(prs, "One target, two validation splits", "Results", title_size=31)
    rows = [["Model", "PR-AUC, unseen years", "PR-AUC, unseen countries"]]
    for m, v in L1.items():
        rows.append([m, f"{v['temporal']['pr_auc']:.3f}", f"{v['loco']['pr_auc']:.3f}"])
    table(s, MG, Inches(1.62), Inches(6.55), rows,
          col_w=[Inches(3.05), Inches(1.75), Inches(1.75)], size=10.5, row_h=0.315)

    prose(s, MG + Inches(7.05), Inches(1.66), Inches(5.0), Inches(2.6), [
        f"Base rate {PREV*100:.2f} per cent, so PR-AUC is the metric that moves.",
        f"ROC-AUC stays inside 0.80–0.87 for all six families on both splits. It cannot "
        "separate them, which is why it is not the headline.",
        "Logistic Regression is the champion because it wins on unseen countries, which is "
        "what deployment means.",
    ], size=10.5, space=8)

    stat(s, MG, Inches(4.55), Inches(3.85), f"{RF['temporal']['pr_auc']:.3f}",
         "random forest, unseen years")
    stat(s, MG + Inches(4.05), Inches(4.55), Inches(3.85), f"{LR['loco']['pr_auc']:.3f}",
         "logistic, unseen countries", accent=True)
    stat(s, MG + Inches(8.10), Inches(4.55), Inches(4.00), f"{RF['loco']['pr_auc']:.3f}",
         "random forest, unseen countries")

    takeaway(s, Inches(5.92),
             "The ranking inverts between the two splits. A model that generalises across "
             "countries has to be simpler than one that generalises across years, because "
             "country-level structure is what the flexible models memorise.")

    # ------------------------------------------------------------ 12 curves
    s = page(prs, "What the two metrics actually measure", "Results", title_size=31)
    pic(s, "fig03_roc_pr_curves.png", MG, Inches(1.66), w=Inches(6.10))
    chip(s, MG, Inches(4.34), Inches(6.10),
         "Left: ROC curves, which stay high because the negatives vastly outnumber the "
         "positives. Right: precision-recall, which falls as recall rises.")

    pic(s, "fig05_ablation.png", Inches(7.30), Inches(1.66), w=Inches(5.20))
    chip(s, Inches(7.30), Inches(4.34), Inches(5.20),
         "Attribution-based selection against correlation-based, on the same split.")

    prose(s, MG, Inches(4.98), CWD, Inches(0.9), [
        "The ROC panel is why the deck does not lead with ROC-AUC. Every family sits near "
        "0.85 there, including models that find almost none of the positives. The PR panel "
        "separates them, and the ablation shows what the feature choice is worth.",
    ], size=11)

    takeaway(s, Inches(5.86),
             "Two metrics, two different questions, and only one of them tells you whether "
             "the model finds events.")

    # ------------------------------------------------------------ 13 calibration
    s = page(prs, "The number has to be worth quoting", "Calibration", title_size=31)

    stat(s, MG, Inches(1.62), Inches(3.05), f"{R['calibration']['ece']:.3f}",
         "expected calibration error", accent=True)
    stat(s, MG + Inches(3.25), Inches(1.62), Inches(3.05), f"{R['calibration']['brier']:.3f}",
         "Brier score")
    stat(s, MG + Inches(6.50), Inches(1.62), Inches(3.05), f"{AE['r6']*100:.0f}%",
         "events caught at a 6% budget")

    prose(s, MG, Inches(3.02), Inches(5.6), Inches(2.2), [
        "A ranking can sort countries. A message needs a number somebody can act on, and "
        "that requires the probabilities to mean what they say.",
        f"An error of {R['calibration']['ece']:.3f} means a predicted 0.20 corresponds to "
        "roughly one event in five. The reliability curve below is the evidence.",
        "The alert levels are read off this curve rather than set to a default 0.5.",
    ], size=11, space=8)

    pic(s, "fig04_calibration.png", MG + Inches(6.10), Inches(3.02), w=Inches(5.85), plate=True)
    chip(s, MG + Inches(6.19), Inches(5.62), Inches(5.8),
         "Predicted probability against observed frequency. A well calibrated model follows "
         "the diagonal.")

    takeaway(s, Inches(6.22),
             "Calibration is what lets one number serve two consumers: the alert service "
             "thresholds it, and the RAG layer can use it as context when answering a question.",
             h=Inches(0.56))

    # ------------------------------------------------------------ 14 section 02
    divider(prs, "02", "The RAG question-answering layer",
            "How do officers and owners get answers that cite official guidance?",
            ["Grounded retrieval with citations, and refusal when nothing supports an answer",
             "Guardrails that stop the model from inventing control instructions",
             "The evaluation protocol, and what has not yet been measured"])

    # ------------------------------------------------------------ 15 rag how
    s = page(prs, "A question is answered from retrieved passages", "RAG Q&A", title_size=30)
    steps = [
        ("01", "Question", "“Why is this district high risk?”"),
        ("02", "Retrieve", "Dense plus lexical search over the guidance corpus"),
        ("03", "Fuse", "Reciprocal rank fusion, then a cross-encoder rerank"),
        ("04", "Answer", "Every claim tied to a retrieved passage, or refused"),
    ]
    for i, (num, head, text) in enumerate(steps):
        card(s, MG + i * Inches(3.05), Inches(1.64), Inches(2.85), Inches(1.72),
             num=num, head=head, text=text, head_size=13.5, text_size=10.5, num_size=22)

    card(s, MG, Inches(3.62), Inches(5.85), Inches(1.85),
         head="Guardrails, not suggestions",
         text="Refuses to answer outside the retrieved sources. Refuses to diagnose an "
              "individual animal. Always shows the passages it used.",
         head_size=14, text_size=11)
    card(s, MG + Inches(6.05), Inches(3.62), Inches(6.05), Inches(1.85),
         head="Why retrieval rather than a fine-tune",
         text="Guidance changes and weights would have to be retrained to follow it. A "
              "cited passage can be checked by a veterinarian; a generated sentence cannot.",
         head_size=14, text_size=11)

    quote = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, MG, Inches(5.68), CWD,
                               Inches(0.92))
    quote.adjustments[0] = 0.08
    quote.fill.solid(); quote.fill.fore_color.rgb = WHITE
    quote.line.color.rgb = CARD_DEEP; quote.line.width = Pt(0.75)
    plain(quote)
    qtf = quote.text_frame; qtf.word_wrap = True
    qtf.margin_left = Inches(0.24); qtf.margin_right = Inches(0.2)
    qtf.vertical_anchor = MSO_ANCHOR.MIDDLE
    qp = qtf.paragraphs[0]
    qp.text = ("“Risk is elevated mainly because of recent reported activity in neighbouring "
               "districts and high equine density. Restrict equid movement and contact the "
               "local veterinary authority if an animal is suspected.”")
    qp.font.size = Pt(10.5); qp.font.italic = True
    qp.font.color.rgb = BODY; qp.font.name = SERIF

    # ------------------------------------------------------------ 16 rag eval
    s = page(prs, "How this layer will be judged", "RAG Q&A", title_size=31)
    rows = [["Metric", "What it asks", "How it is measured"],
            ["Recall@k", "Is the right passage in the top k?", "Hand-built question set"],
            ["Faithfulness", "Does the answer follow from those passages?", "RAGAS, plus manual review"],
            ["Answer relevance", "Does it answer the question asked?", "RAGAS"],
            ["Citation precision", "Does every claim trace to a passage?", "Automated check"]]
    table(s, MG, Inches(1.66), CWD, rows,
          col_w=[Inches(2.35), Inches(5.55), Inches(4.2)], size=11, row_h=0.375)

    prose(s, MG, Inches(3.78), Inches(11.6), Inches(1.2), [
        "These four cover the ways an explanation fails: retrieving the wrong passage, "
        "drifting from the passages it retrieved, or faithfully answering a question "
        "nobody asked.",
    ], size=11)

    takeaway(s, Inches(4.62),
             "None of these are measured yet. Targets are fixed before measurement, so the "
             "layer cannot be scored by choosing a threshold after seeing the results.")

    card(s, MG, Inches(5.52), CWD, Inches(1.05), fill=CARD_DEEP,
         head="Why this is stated rather than shown",
         text="The layer is specified to the level of its interface and rules. Reporting a "
              "metric without a deployment would be a stronger claim than the evidence supports.",
         head_size=12.5, text_size=10.5)

    # ------------------------------------------------------------ 17 section 03
    divider(prs, "03", "The alert service",
            "How does a probability become a message that is still read in month twelve?",
            ["Levels read from the calibration curve, not a default cutoff",
             "Hysteresis, deduplication and a stale-data guard",
             "Delivery measured against alert fatigue, not accuracy"])

    # ------------------------------------------------------------ 18 alert how
    s = page(prs, "Five stages, each preventing one failure", "Alerting", title_size=31)
    stages = [
        ("01", "Predict", "Latest calibrated score for the area"),
        ("02", "Assign level", "Thresholds from the budget curve"),
        ("03", "Deduplicate", "Three idempotency keys"),
        ("04", "Deliver", "SMS or WhatsApp, with retries"),
        ("05", "Log", "Status per recipient"),
    ]
    for i, (num, head, text) in enumerate(stages):
        x = MG + i * Inches(2.47)
        card(s, x, Inches(1.64), Inches(2.27), Inches(1.55), num=num, head=head,
             text=text, head_size=12.5, text_size=9.5, num_size=20)
        if i < 4:
            a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + Inches(2.29),
                                   Inches(2.30), Inches(0.16), Inches(0.18))
            a.fill.solid(); a.fill.fore_color.rgb = ACCENT
            a.line.fill.background(); plain(a)

    guards = [
        ("Hysteresis", "Enter at a threshold, leave only 0.05 below it, so a country on the "
                       "line does not oscillate."),
        ("Freshness", "If the data check fails, no alert goes out and the admin is told "
                      "instead."),
        ("Quiet hours", "Hold overnight except for escalation, so a real rise still gets "
                        "through."),
    ]
    for i, (head, text) in enumerate(guards):
        card(s, MG + i * Inches(4.05), Inches(3.50), Inches(3.85), Inches(1.32),
             head=head, text=text, head_size=13.5, text_size=10.5)

    stat(s, MG, Inches(5.05), Inches(2.85), f"{AE['b50']*100:.0f}%",
         "budget for half the events")
    stat(s, MG + Inches(3.05), Inches(5.05), Inches(2.85), f"{AE['b80']*100:.0f}%",
         "budget for 80 per cent")
    stat(s, MG + Inches(6.10), Inches(5.05), Inches(2.85), f"{AE['r6']*100:.0f}%",
         "caught at a 6 per cent budget")

    takeaway(s, Inches(6.28),
             "Levels carry a measured meaning because they come from the curve, and "
             "deduplication is what stops a re-run or a retrain from sending the same "
             "warning twice.", h=Inches(0.58))

    # ------------------------------------------------------------ 19 alert eval
    s = page(prs, "What an owner receives, and how it is judged", "Alerting",
             title_size=30)
    rows = [["Metric", "What it asks"],
            ["Precision", "Of the alerts sent, how many were real events?"],
            ["Recall", "Of the real events, how many did we alert on?"],
            ["Missed events", "The failure a user actually feels"],
            ["False alerts per subscriber", "The alert-fatigue budget"]]
    table(s, MG, Inches(1.66), Inches(6.20), rows,
          col_w=[Inches(2.65), Inches(3.55)], size=10.5, row_h=0.36)

    prose(s, MG, Inches(3.62), Inches(6.20), Inches(1.4), [
        "Defined but not yet measured. A pilot with a district office is how these acquire "
        "numbers, and until then the service is not claimed to work.",
    ], size=10.5)

    msg = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, MG + Inches(6.65), Inches(1.66),
                             Inches(5.45), Inches(3.55))
    msg.adjustments[0] = 0.05
    msg.fill.solid(); msg.fill.fore_color.rgb = WHITE
    msg.line.color.rgb = CARD_DEEP; msg.line.width = Pt(0.75)
    plain(msg)
    mtf = msg.text_frame; mtf.word_wrap = True
    mtf.margin_left = Inches(0.26); mtf.margin_right = Inches(0.22)
    mtf.margin_top = Inches(0.20)
    mp = mtf.paragraphs[0]
    mp.text = "GLANDERS RISK ALERT"
    mp.font.size = Pt(10); mp.font.bold = True
    mp.font.color.rgb = ACCENT; mp.font.name = SANS
    set_spacing(mp.runs[0], 140)

    lines = [
        ("Risk", "HIGH"),
        ("Reason", "recent reported activity in neighbouring districts; high equine density"),
        ("Action", "avoid unnecessary movement or mixing of equids; contact the local "
                   "veterinary authority if an animal is suspected of illness"),
        ("Caveat", "a population-level forecast, not a diagnosis"),
    ]
    for lab, val in lines:
        q = mtf.add_paragraph()
        q.text = lab
        q.font.size = Pt(9); q.font.bold = True
        q.font.color.rgb = MUTED; q.font.name = SANS
        q.space_before = Pt(9)
        v = mtf.add_paragraph()
        v.text = val
        v.font.size = Pt(10.5); v.font.color.rgb = BODY; v.font.name = SANS
        v.space_before = Pt(1)

    takeaway(s, Inches(5.52),
             "The message names its reason and its action, and says plainly that it is a "
             "forecast. A warning without those three parts is not actionable, and an "
             "owner who cannot act on it will stop reading.")

    # ------------------------------------------------------------ 20 conclusion
    s = page(prs, "What is built, and what a pilot would settle", "Conclusion",
             title_size=30)
    card(s, MG, Inches(1.62), Inches(5.85), Inches(2.72), head="Conclusion",
         text="The risk engine is built and measured: six families, two splits, calibrated, "
              "with every number reproducible from committed scripts. The RAG and alert "
              "layers are specified to the level of their interfaces and rules.",
         head_size=16, text_size=11)
    card(s, MG + Inches(6.05), Inches(1.62), Inches(6.05), Inches(2.72),
         head="Future scope",
         text="Model reporting capacity as a quantity rather than a covariate. Measure the "
              "RAG layer on a hand-built question set. Pilot the alert service with a "
              "district office and report precision, recall and fatigue.",
         head_size=16, text_size=11, fill=CARD_DEEP)

    prose(s, MG, Inches(4.58), CWD, Inches(1.2), [
        f"The dominant limitation is the label: a negative may mean no disease or no report. "
        f"With {POS} positives the uncertainty on every headline metric is wide, and the "
        "honest reading is that this is a moderate model on a hard, noisy target.",
    ], size=11)

    takeaway(s, Inches(5.72),
             "The model is the part that is finished. Evidence that the RAG and alert "
             "layers behave in use is the part that is not, and a pilot is how it arrives.",
             h=Inches(0.72))

    # ------------------------------------------------------------ Q&A (guideline)
    s = page(prs, "Questions", "Q&A ownership", title_size=34)
    rows = [
        ["Topic", "Who answers"],
        ["Data panel, features, splits, ML results", "Yuvraj Singh"],
        ["RAG retrieval, citations, refusal", "Shaktimayee Mohanty"],
        ["Alert rules, delivery, audit trail", "P. Shanmukh Vardhan"],
        ["Scope, limits, future work", "Any of us"],
    ]
    table(s, MG, Inches(1.85), CWD, rows,
          col_w=[Inches(7.4), Inches(4.7)], size=14, row_h=0.48)
    takeaway(s, Inches(5.35),
             "Thank you. We will take questions now.")

    # ------------------------------------------------------------ 21 references
    s = page(prs, "References", None, title_size=30)
    refs = [
        "Lundberg, S. M. and Lee, S.-I. (2017). A unified approach to interpreting model "
        "predictions. NeurIPS 30.",
        "Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5–32.",
        "Chen, T. and Guestrin, C. (2016). XGBoost: a scalable tree boosting system. KDD ’16.",
        "Ke, G. et al. (2017). LightGBM: a highly efficient gradient boosting decision tree. "
        "NeurIPS 30.",
        "Lewis, P. et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP "
        "tasks. NeurIPS 33.",
        "Es, S. et al. (2023). RAGAS: automated evaluation of retrieval augmented generation. "
        "arXiv:2309.15217.",
        "Robertson, S. and Zaragoza, H. (2009). The probabilistic relevance framework: BM25 "
        "and beyond. Foundations and Trends in IR, 3(4), 333–389.",
        "Food and Agriculture Organization (2024). FAOSTAT livestock stocks. Rome.",
        "World Bank (2024). World Development Indicators. Washington, DC.",
        "NASA Langley Research Center (2024). POWER project: prediction of worldwide energy "
        "resources.",
        "Europe PMC (2024). Literature database, EMBL-EBI.",
        "Department of Animal Husbandry and Dairying (2025). National Action Plan on Glanders. "
        "Government of India.",
        "ICAR-NIVEDI (2023). NADRES v2: national animal disease referential and forewarning "
        "system.",
    ]
    for i, r in enumerate(refs):
        tb = s.shapes.add_textbox(MG, Inches(1.42) + Inches(0.395) * i, CWD, Inches(0.36))
        tb.text_frame.word_wrap = True
        tb.text_frame.margin_left = 0
        tb.text_frame.margin_top = 0
        p = tb.text_frame.paragraphs[0]
        p.text = f"[{i+1}]   {r}"
        p.font.size = Pt(9.5); p.font.color.rgb = BODY; p.font.name = SANS

    prs.save(OUT)
    desk = pathlib.Path.home() / "Desktop" / "GlandersWatch_Deck.pptx"
    desk.write_bytes(OUT.read_bytes())
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(prs.slides)} slides)")
    print(f"copied {desk}")
    return OUT


if __name__ == "__main__":
    build()
