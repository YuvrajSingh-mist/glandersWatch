"""Build a simple, report-aligned presentation deck.

Run:  .venv/bin/python src/15_make_deck.py

Design: white slides, navy/orange accent, tables and prose. Charts are taken
from GlandersWatch_Final_v2.pdf (figures/from_report/), not decorative art.
Numbers come from reports/*.json so they stay pipeline-synced.
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
from pptx.oxml.ns import qn
from lxml import etree

ROOT = pathlib.Path(__file__).resolve().parents[1]
REP, FIG = ROOT / "reports", ROOT / "figures"
RFIG = FIG / "from_report"
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

_rank = SEL["ranking"]
ATTR_SHARE = sum(r["mean_abs_shap"] for r in _rank[: SEL["top_k"]]) / (
    sum(r["mean_abs_shap"] for r in _rank) or 1.0)

# ---------------------------------------------------------------- palette (simple)
BG = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1A, 0x1A, 0x1A)
BODY = RGBColor(0x33, 0x33, 0x33)
MUTED = RGBColor(0x66, 0x66, 0x66)
LINE = RGBColor(0xD0, 0xD0, 0xD0)
SOFT = RGBColor(0xF5, 0xF5, 0xF5)
ACCENT = RGBColor(0xC4, 0x4E, 0x1C)
NAVY = RGBColor(0x06, 0x1E, 0x5E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PALE = RGBColor(0xC3, 0xCE, 0xE4)

SERIF = "Georgia"
SANS = "Calibri"

W, H = Inches(13.333), Inches(7.5)
MG = Inches(0.55)
CWD = W - 2 * MG
FOOT = "GlandersWatch  ·  B.Tech Project  ·  IIIT Bhubaneswar"


def alert_econ() -> dict:
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
_PAGE = [0]


def plain(shape):
    shape.shadow.inherit = False
    return shape


def ground(s):
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    bg.fill.solid(); bg.fill.fore_color.rgb = BG
    bg.line.fill.background(); plain(bg)
    # thin top accent
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Inches(0.06))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background(); plain(bar)
    return bg


def footer(s, pg: int):
    rule = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, MG, Inches(7.05), CWD, Inches(0.01))
    rule.fill.solid(); rule.fill.fore_color.rgb = LINE
    rule.line.fill.background(); plain(rule)

    f = s.shapes.add_textbox(MG, Inches(7.12), Inches(9.5), Inches(0.28))
    p = f.text_frame.paragraphs[0]
    p.text = FOOT
    p.font.size = Pt(10); p.font.color.rgb = MUTED; p.font.name = SANS

    nb = s.shapes.add_textbox(W - MG - Inches(1.0), Inches(7.12), Inches(1.0), Inches(0.28))
    np_ = nb.text_frame.paragraphs[0]
    np_.text = str(pg)
    np_.alignment = PP_ALIGN.RIGHT
    np_.font.size = Pt(10); np_.font.color.rgb = MUTED; np_.font.name = SANS


def page(prs, title: str, eyebrow: str | None = None, title_size: int = 28):
    _PAGE[0] += 1
    s = prs.slides.add_slide(prs.slide_layouts[6])
    ground(s)

    y = Inches(0.28)
    if eyebrow:
        e = s.shapes.add_textbox(MG, y, Inches(8.0), Inches(0.28))
        ep = e.text_frame.paragraphs[0]
        ep.text = eyebrow.upper()
        ep.font.size = Pt(11); ep.font.bold = True
        ep.font.color.rgb = ACCENT; ep.font.name = SANS
        y = Inches(0.52)

    t = s.shapes.add_textbox(MG, y, CWD, Inches(0.55))
    tp = t.text_frame.paragraphs[0]
    tp.text = title
    tp.font.size = Pt(title_size); tp.font.bold = True
    tp.font.color.rgb = INK; tp.font.name = SERIF

    rule = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, MG, Inches(1.15),
                              Inches(0.70), Inches(0.035))
    rule.fill.solid(); rule.fill.fore_color.rgb = ACCENT
    rule.line.fill.background(); plain(rule)

    footer(s, _PAGE[0])
    return s


def prose(s, x, y, w, h, lines, size=13, space=8, color=BODY, bullet="•  "):
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


def box(s, x, y, w, h, fill=SOFT):
    b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    b.fill.solid(); b.fill.fore_color.rgb = fill
    b.line.color.rgb = LINE; b.line.width = Pt(0.75)
    plain(b)
    return b


def labeled(s, x, y, w, h, num, head, text, head_size=15, text_size=12):
    box(s, x, y, w, h)
    tb = s.shapes.add_textbox(x + Inches(0.16), y + Inches(0.12),
                              w - Inches(0.28), h - Inches(0.20))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"{num}  {head}"
    p.font.size = Pt(head_size); p.font.bold = True
    p.font.color.rgb = INK; p.font.name = SERIF
    p.space_after = Pt(6)
    p2 = tf.add_paragraph()
    p2.text = text
    p2.font.size = Pt(text_size); p2.font.color.rgb = BODY; p2.font.name = SANS
    return tb


def stat(s, x, y, w, value, label, h=Inches(0.95)):
    box(s, x, y, w, h)
    tb = s.shapes.add_textbox(x + Inches(0.14), y + Inches(0.10),
                              w - Inches(0.24), h - Inches(0.16))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = value
    p.font.size = Pt(22); p.font.bold = True
    p.font.color.rgb = NAVY; p.font.name = SERIF
    p2 = tf.add_paragraph()
    p2.text = label
    p2.font.size = Pt(11); p2.font.color.rgb = BODY; p2.font.name = SANS
    return tb


def table(s, x, y, w, rows, col_w=None, size=12, row_h=0.32, right_cols=()):
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
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            para = cell.text_frame.paragraphs[0]
            para.font.size = Pt(size); para.font.name = SANS
            if c in right_cols:
                para.alignment = PP_ALIGN.RIGHT
            if r == 0:
                para.font.bold = True
                para.font.color.rgb = WHITE
                cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
            else:
                para.font.color.rgb = INK
                cell.fill.solid()
                cell.fill.fore_color.rgb = SOFT if r % 2 else BG
            # remove table borders for a cleaner look
            for border_name in ("lnL", "lnR", "lnT", "lnB"):
                ln = cell._tc.get_or_add_tcPr().find(qn(f"a:{border_name}"))
                # python-pptx creates borders lazily; set via tcPr
            tcPr = cell._tc.get_or_add_tcPr()
            for edge in ("lnL", "lnR", "lnT", "lnB"):
                existing = tcPr.find(qn(f"a:{edge}"))
                if existing is not None:
                    tcPr.remove(existing)
                el = etree.SubElement(tcPr, qn(f"a:{edge}"))
                el.set("w", "0")
                el.set("cap", "flat")
                el.set("cmpd", "sng")
                el.set("algn", "ctr")
                sf = etree.SubElement(el, qn("a:solidFill"))
                srgb = etree.SubElement(sf, qn("a:srgbClr"))
                srgb.set("val", "D0D0D0" if r == 0 else "E8E8E8")
    return tbl


def caption(s, x, y, w, text):
    tb = s.shapes.add_textbox(x, y, w, Inches(0.40))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(10); p.font.italic = True
    p.font.color.rgb = MUTED; p.font.name = SANS
    return tb


def pic(s, name, x, y, w=None, h=None, from_report=True):
    path = (RFIG / name) if from_report else (FIG / name)
    if not path.exists():
        # fall back to figures/
        path = FIG / name
    if not path.exists():
        return None
    kwargs = {}
    if w is not None:
        kwargs["width"] = w
    if h is not None:
        kwargs["height"] = h
    return s.shapes.add_picture(str(path), x, y, **kwargs)


def takeaway(s, y, text, h=Inches(0.55)):
    box(s, MG, y, CWD, h, fill=SOFT)
    tb = s.shapes.add_textbox(MG + Inches(0.18), y + Inches(0.08),
                              CWD - Inches(0.30), h - Inches(0.12))
    tf = tb.text_frame; tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(12); p.font.color.rgb = INK; p.font.name = SANS


def divider(prs, num: str, title: str, question: str, items: list[str]):
    _PAGE[0] += 1
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    bg.fill.solid(); bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background(); plain(bg)

    n = s.shapes.add_textbox(MG, Inches(2.0), Inches(3.0), Inches(0.8))
    np_ = n.text_frame.paragraphs[0]
    np_.text = num
    np_.font.size = Pt(48); np_.font.bold = True
    np_.font.color.rgb = ACCENT; np_.font.name = SERIF

    t = s.shapes.add_textbox(MG, Inches(2.85), Inches(10.5), Inches(0.8))
    tp = t.text_frame.paragraphs[0]
    tp.text = title
    tp.font.size = Pt(34); tp.font.bold = True
    tp.font.color.rgb = WHITE; tp.font.name = SERIF

    q = s.shapes.add_textbox(MG, Inches(3.75), Inches(10.5), Inches(0.6))
    qp = q.text_frame.paragraphs[0]
    qp.text = question
    qp.font.size = Pt(14); qp.font.color.rgb = PALE; qp.font.name = SANS

    c = s.shapes.add_textbox(MG, Inches(4.55), Inches(10.5), Inches(1.6))
    ctf = c.text_frame; ctf.word_wrap = True
    for i, item in enumerate(items):
        p = ctf.paragraphs[0] if i == 0 else ctf.add_paragraph()
        p.text = "—  " + item
        p.font.size = Pt(13); p.font.color.rgb = WHITE; p.font.name = SANS
        p.space_after = Pt(6)
    return s


def build() -> pathlib.Path:
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    _PAGE[0] = 0

    # ------------------------------------------------------------ 1 cover
    s = prs.slides.add_slide(prs.slide_layouts[6])
    base = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    base.fill.solid(); base.fill.fore_color.rgb = NAVY
    base.line.fill.background(); plain(base)

    logo = FIG / "iiit_logo.png"
    if logo.exists():
        s.shapes.add_picture(str(logo), W - Inches(1.9), Inches(0.45), width=Inches(1.2))

    e = s.shapes.add_textbox(MG, Inches(1.6), Inches(10), Inches(0.35))
    ep = e.text_frame.paragraphs[0]
    ep.text = "B.TECH PROJECT REPORT"
    ep.font.size = Pt(12); ep.font.bold = True
    ep.font.color.rgb = ACCENT; ep.font.name = SANS

    t = s.shapes.add_textbox(MG, Inches(2.1), Inches(11), Inches(0.9))
    p = t.text_frame.paragraphs[0]
    p.text = "GlandersWatch"
    p.font.size = Pt(44); p.font.bold = True
    p.font.color.rgb = WHITE; p.font.name = SERIF

    sub = s.shapes.add_textbox(MG, Inches(3.05), Inches(11), Inches(0.7))
    sp = sub.text_frame.paragraphs[0]
    sp.text = ("Next-year risk prediction, grounded Q&A and owner alerting "
               "for a neglected zoonosis")
    sp.font.size = Pt(16); sp.font.color.rgb = PALE; sp.font.name = SANS

    meta = s.shapes.add_textbox(MG, Inches(4.3), Inches(10), Inches(2.2))
    mtf = meta.text_frame; mtf.word_wrap = True
    lines = [
        ("Supervisor", "Dr. Sangita Dhara"),
        ("Presented by",
         "P. Shanmukh Vardhan (B123089)  ·  Shaktimayee Mohanty (B123118)  ·  "
         "Yuvraj Singh (B123153)"),
        ("Department", "Computer Science and Engineering  ·  IIIT Bhubaneswar  ·  Nov 2026"),
    ]
    first = True
    for lab, val in lines:
        p = mtf.paragraphs[0] if first else mtf.add_paragraph()
        first = False
        p.text = f"{lab}:  {val}"
        p.font.size = Pt(13); p.font.color.rgb = WHITE; p.font.name = SANS
        p.space_after = Pt(10)

    # ------------------------------------------------------------ 2 outline
    s = page(prs, "Presentation outline", "Running order")
    table(s, MG, Inches(1.45), CWD, [
        ["#", "Segment", "Presenter", "Owns Q&A on"],
        ["1", "Problem, objectives, platform", "Yuvraj Singh", "Scope, label, contracts"],
        ["2", "Data, features, models, results", "Yuvraj Singh", "Splits, metrics, champion"],
        ["3", "RAG explanation layer", "Shaktimayee Mohanty",
         "Evidence separation, citations, PFPT/CAIS"],
        ["4", "Alerting system", "P. Shanmukh Vardhan", "Rules, delivery, audit"],
        ["5", "Limits, future work, close", "All three", "Open questions together"],
    ], col_w=[Inches(0.55), Inches(4.4), Inches(3.2), Inches(4.0)],
       size=13, row_h=0.42)
    takeaway(s, Inches(5.55),
             "Aligned to Final_v2 (~41 pages). Charts on later slides are taken from the "
             "report PDF itself. Measured results are only for next-year (t+1) prediction.")

    # ------------------------------------------------------------ 3 intro
    s = page(prs, "A disease that still has no forecast", "Introduction")
    labeled(s, MG, Inches(1.40), Inches(5.95), Inches(2.0), "01", "The organism",
            "Glanders is a bacterial zoonosis of equids caused by Burkholderia mallei. "
            "Notifiable, frequently fatal, with no environmental reservoir.")
    labeled(s, MG + Inches(6.15), Inches(1.40), Inches(5.95), Inches(2.0), "02", "The gap",
            "Surveillance describes what already happened. Published ML work on this "
            "disease stops at laboratory identification. No population-level risk model "
            "has been reported.")
    prose(s, MG, Inches(3.65), CWD, Inches(1.6), [
        "Indian surveillance, 2019–2023, found 728 seropositive equids in 138 districts.",
        "This project adds three independently deployable pieces behind fixed contracts:",
        "- a calibrated next-year risk model,",
        "- a RAG explanation layer that answers from official guidance (or refuses),",
        "- an alert service that sends few enough messages to stay readable.",
    ], size=14, space=6)
    takeaway(s, Inches(5.85),
             "Components talk through versioned schemas, so none hardcodes the disease "
             "and each can degrade without failing the others.")

    # ------------------------------------------------------------ 4 why + report fig 1.1
    s = page(prs, "Population at risk is not the same as damage", "Why it matters",
             title_size=26)
    stat(s, MG, Inches(1.35), Inches(3.9), "5.50 lakh", "equids in India, 2019")
    stat(s, MG + Inches(4.1), Inches(1.35), Inches(3.9), "728", "seropositive, 2019–23")
    stat(s, MG + Inches(8.2), Inches(1.35), Inches(3.9), "138", "districts affected")

    pic(s, "report_fig1_1.png", MG, Inches(2.50), w=Inches(12.2))
    caption(s, MG, Inches(5.55), CWD,
            "Report Figure 1: Panel A exposed population by species; "
            "Panel B documented events per year (tracks publishing as much as disease).")
    takeaway(s, Inches(6.05),
             "The target is a documented event rather than raw incidence, because "
             "documentation follows publishing capacity.")

    # ------------------------------------------------------------ 5 problem
    s = page(prs, "Problem statement", "Definition")
    box(s, MG, Inches(1.40), CWD, Inches(0.85))
    tb = s.shapes.add_textbox(MG + Inches(0.2), Inches(1.52), CWD - Inches(0.35), Inches(0.65))
    tp = tb.text_frame.paragraphs[0]
    tp.text = ("Given a country's features in year t, predict whether glanders is "
               "documented in that country in year t + 1.")
    tp.font.size = Pt(16); tp.font.bold = True
    tp.font.color.rgb = INK; tp.font.name = SERIF

    labeled(s, MG, Inches(2.50), Inches(5.95), Inches(2.15), "01", "The label",
            "One country-year is positive if a glanders occurrence is reported from that "
            "country in that year. Features come only from the year before.")
    labeled(s, MG + Inches(6.15), Inches(2.50), Inches(5.95), Inches(2.15), "02",
            "The difficulty",
            f"{POS} positives in {ROWS:,} rows. A model that always says “no” is "
            f"{100 * (1 - PREV):.0f}% accurate and worthless — accuracy and ROC-AUC "
            "are not used to rank models.")
    takeaway(s, Inches(5.20),
             f"Base rate {PREV * 100:.2f}%. Precision-recall AUC is the primary metric "
             f"because it moves when a model finds the {POS} positives.")

    # ------------------------------------------------------------ 6 objectives
    s = page(prs, "Project objectives", "Scope")
    objs = [
        ("01", "Prediction as a service",
         "Package a calibrated next-year risk model as a versioned artefact behind a REST interface."),
        ("02", "Grounded Q&A",
         "Build a retrieval-augmented explanation layer that answers from official guidance, "
         "cites every claim, refuses when unsupported, and keeps forecast facts separate from guidance."),
        ("03", "Owner alerts",
         "Convert a calibrated probability into few enough messages that they are read."),
    ]
    for i, (num, head, text) in enumerate(objs):
        labeled(s, MG, Inches(1.40) + i * Inches(1.35), CWD, Inches(1.20),
                num, head, text, head_size=16, text_size=13)
    takeaway(s, Inches(5.70),
             "Objective 01 has measured results. 02 and 03 are specified contracts with "
             "evaluation protocols, not presented as measured field performance.")

    # ------------------------------------------------------------ 7 users
    s = page(prs, "Who the system is for", "Use")
    users = [
        ("01", "District veterinary officer",
         "Where to pre-position testing and movement checks, before the report arrives."),
        ("02", "Equine owner",
         "Whether this is the month to restrict movement, in a language they read."),
        ("03", "State planner",
         "A single scale on which districts can be compared for resources."),
    ]
    for i, (num, head, text) in enumerate(users):
        labeled(s, MG + i * Inches(4.1), Inches(1.45), Inches(3.9), Inches(2.2),
                num, head, text)
    takeaway(s, Inches(4.20),
             "A warning system that fires for every area every month is ignored by month "
             "twelve. Alert budget is a design constraint, not a tuning parameter.")

    # ------------------------------------------------------------ section 01
    divider(prs, "01", "The risk engine",
            "Can a country's next year be forecast from its last?",
            ["Four public sources assembled into a country-year panel",
             "Eight features chosen by attribution rather than correlation",
             "Six model families, two validation splits, calibration check"])

    # ------------------------------------------------------------ architecture (report fig 3.1)
    s = page(prs, "Three components behind fixed contracts", "Architecture",
             title_size=26)
    pic(s, "fig_architecture.png", MG + Inches(1.8), Inches(1.35), w=Inches(8.6))
    caption(s, MG, Inches(5.45), CWD,
            "Report Figure 2: ML risk engine, RAG explanation layer, and alert service; "
            "each independently deployable.")
    takeaway(s, Inches(5.95),
             "Coupling alert delivery to LLM latency would make the risk model hard to "
             "test on its own — so the three jobs stay separate.")

    # ------------------------------------------------------------ data
    s = page(prs, "Four public sources, none built for this disease", "Data",
             title_size=26)
    srcs = [
        ("01", "Europe PMC", "Occurrence events from abstracts: the label."),
        ("02", "FAOSTAT", "Horse, ass and mule head counts: exposure."),
        ("03", "World Bank", "Development and connectivity: context."),
        ("04", "NASA POWER", "Temperature, humidity, rainfall: environment."),
    ]
    for i, (num, head, text) in enumerate(srcs):
        labeled(s, MG + i * Inches(3.1), Inches(1.35), Inches(2.95), Inches(1.45),
                num, head, text, head_size=13, text_size=11)

    stat(s, MG, Inches(3.20), Inches(2.9), f"{ROWS:,}", "modelling rows")
    stat(s, MG + Inches(3.1), Inches(3.20), Inches(2.9), f"{NC}", "countries")
    stat(s, MG + Inches(6.2), Inches(3.20), Inches(2.9), f"{POS}", "positives")
    stat(s, MG + Inches(9.3), Inches(3.20), Inches(2.85), f"{PREV*100:.2f}%", "prevalence")
    takeaway(s, Inches(4.50),
             "The next slide shows the three label charts from the report "
             "(Figures 8 to 10), stacked for readability.")

    # ------------------------------------------------------------ label figs 8-10
    s = page(prs, "How the label looks", "Data", title_size=26)
    panels = [
        ("fig10a_label_volume.png", "Fig 8  Annual positives and prevalence"),
        ("fig10b_label_concentration.png", "Fig 9  Positive years per country"),
        ("fig10c_label_region.png", "Fig 10  Prevalence by World Bank region"),
    ]
    y = Inches(1.30)
    for name, cap in panels:
        pic(s, name, MG + Inches(1.6), y, w=Inches(9.9), from_report=False)
        caption(s, MG + Inches(1.6), y + Inches(1.55), Inches(9.9), cap)
        y += Inches(1.85)

    # ------------------------------------------------------------ method + training fig
    s = page(prs, "From sources to a calibrated probability", "Method", title_size=26)
    pic(s, "fig_training.png", MG, Inches(1.35), w=Inches(6.3))
    caption(s, MG, Inches(5.00), Inches(6.3),
            "Report Figure 3: Training pipeline (chronological split before any model sees data).")

    prose(s, MG + Inches(6.55), Inches(1.40), Inches(5.5), Inches(4.2), [
        "Temporal split: train 2005–2017 (~68%), test 2018–2023 (~32%).",
        "Country split: whole countries held out — the deployment-like test.",
        "Feature ranking uses training years only.",
        "",
        "Six families trained; Logistic Regression is the champion on unseen countries.",
        "",
        f"Eight of {SEL['n_candidates']} candidates kept "
        f"({ATTR_SHARE*100:.0f}% of total SHAP attribution).",
    ], size=13, space=7)
    takeaway(s, Inches(5.55),
             "Country codes and calendar years are identifiers and never enter the model.")

    # ------------------------------------------------------------ evaluation fig
    s = page(prs, "How one trained model is scored", "Evaluation", title_size=26)
    pic(s, "fig_evaluation.png", MG + Inches(2.2), Inches(1.30), w=Inches(8.8))
    caption(s, MG, Inches(5.55), CWD,
            "Report Figure 4: Evaluation pipeline: three scoring paths for one fitted model.")
    takeaway(s, Inches(6.05),
             "PR-AUC is the headline metric. ROC-AUC stays high for all families and "
             "cannot separate them on this imbalance.")

    # ------------------------------------------------------------ features
    s = page(prs, "Eight features, chosen by attribution", "Features")
    units = {"pop_total": "persons", "years_since_last": "years (99 = never)",
             "temp_mean_anom": "°C from baseline", "internet_pct": "% of population",
             "humidity_anom": "% RH from baseline", "precip_cv": "ratio, sd / mean",
             "log_livestock": "ln(1 + LSU)", "goats": "head"}
    rows = [["#", "Feature", "Unit", "Mean |SHAP|"]]
    for r in SEL["ranking"][: SEL["top_k"]]:
        rows.append([r["rank"], r["feature"], units.get(r["feature"], ""),
                     f"{r['mean_abs_shap']:.3f}"])
    table(s, MG, Inches(1.40), Inches(7.2), rows,
          col_w=[Inches(0.5), Inches(2.4), Inches(2.8), Inches(1.5)],
          size=12, row_h=0.34, right_cols=(0, 3))
    prose(s, MG + Inches(7.5), Inches(1.45), Inches(4.6), Inches(4.0), [
        "SHAP ranks what the model actually uses.",
        "Correlation / MI score features pairwise and miss interactions.",
        "",
        "Population and years since last report rank first: exposure, then history.",
        "",
        "Correlation ranks longitude high; attribution ranks it near the bottom.",
    ], size=13, space=8)
    takeaway(s, Inches(5.70),
             "Selecting on association keeps geography proxies instead of drivers.")

    # ------------------------------------------------------------ results
    s = page(prs, "One target, two validation splits", "Results")
    rows = [["Model", "PR-AUC (unseen years)", "PR-AUC (unseen countries)"]]
    for m, v in L1.items():
        rows.append([m, f"{v['temporal']['pr_auc']:.3f}", f"{v['loco']['pr_auc']:.3f}"])
    table(s, MG, Inches(1.40), Inches(8.0), rows,
          col_w=[Inches(3.4), Inches(2.3), Inches(2.3)], size=12, row_h=0.34)

    prose(s, MG + Inches(8.3), Inches(1.45), Inches(3.8), Inches(3.5), [
        f"Base rate {PREV*100:.2f}%.",
        "",
        f"Random Forest on years: {RF['temporal']['pr_auc']:.3f}",
        f"Logistic on countries: {LR['loco']['pr_auc']:.3f}",
        "",
        f"Calibration ECE: {R['calibration']['ece']:.3f}",
        f"Brier: {R['calibration']['brier']:.3f}",
        f"Events at 6% budget: {AE['r6']*100:.0f}%",
    ], size=13, space=6)
    takeaway(s, Inches(5.55),
             "Ranking inverts between splits. Logistic Regression is champion because "
             "deployment means unseen countries.")

    # ------------------------------------------------------------ section 02
    divider(prs, "02", "The RAG explanation layer",
            "How do officers and owners get answers that cite official guidance?",
            ["Evidence separation: forecast facts vs official guidance",
             "Hybrid retrieval, citations and refusal when unsupported",
             "Baseline RAG metrics plus PFPT/CAIS attribution audit"])

    # ------------------------------------------------------------ evidence separation
    s = page(prs, "Forecast facts and guidance stay on separate paths", "RAG explanation",
             title_size=24)
    labeled(s, MG, Inches(1.40), Inches(5.95), Inches(2.35), "01", "Forecast facts",
            "Probability, risk tier and SHAP contributors explain what the model output "
            "says. They are injected as structured data and never rewritten as causes.")
    labeled(s, MG + Inches(6.15), Inches(1.40), Inches(5.95), Inches(2.35), "02",
            "Official guidance",
            "Retrieved passages from DAHD, WOAH/WHO and lab guidance explain controls. "
            "Tier 1 never loses to open-access literature on a control instruction.")
    prose(s, MG, Inches(4.05), CWD, Inches(1.35), [
        "Design rule: use the forecast to explain the forecast; use official guidance to "
        "explain the recommended action; keep the evidence paths visible.",
        "The layer does not calculate the risk score, diagnose an animal, or issue a "
        "statutory decision. District language in diagrams is a query example, not the "
        "evaluated resolution (country-year).",
    ], size=13, space=7)
    takeaway(s, Inches(5.65),
             "An answer must not imply that a retrieved recommendation caused the forecast, "
             "or that a forecast proves an individual animal is infected.")

    # ------------------------------------------------------------ rag fig
    s = page(prs, "A question is answered from retrieved passages", "RAG explanation",
             title_size=26)
    pic(s, "fig_rag.png", MG + Inches(2.6), Inches(1.25), w=Inches(8.0), h=Inches(4.6))
    caption(s, MG, Inches(5.95), CWD,
            "Report Figure 5: Offline ingestion (top); retrieval, assembly, generation (below).")
    takeaway(s, Inches(6.40),
             "If fewer than two passages clear the relevance floor, the layer refuses "
             "rather than inventing an answer.", h=Inches(0.48))

    # ------------------------------------------------------------ pfpt / cais
    s = page(prs, "Attribution audit: PFPT and CAIS", "RAG explanation", title_size=26)
    table(s, MG, Inches(1.35), CWD, [
        ["Component", "What it does", "Status"],
        ["PFPT",
         "Matched A/B cases: freeze question, area, corpus and retrieval; "
         "change one forecast field; pre-label expected deltas.",
         "Proposed offline"],
        ["CAIS",
         "Split answers into F/G/S claims; score forecast consistency, "
         "guidance attribution and safety separately.",
         "Proposed diagnostic"],
        ["CACS",
         "100 × (F+G+S passes) / (3N). Report with all subscores; "
         "never use the composite alone.",
         "No threshold yet"],
    ], col_w=[Inches(1.5), Inches(8.4), Inches(2.2)], size=12, row_h=0.48)
    prose(s, MG, Inches(4.15), CWD, Inches(1.2), [
        "Surfaces wrong-area/time, stale-SHAP, false-causal, unsupported-citation, "
        "unsafe-advice and missing-disclaimer failures.",
        "Counterfactual evaluation is prior research. The project-specific value is this "
        "attribution audit for GlandersWatch, not inventing the method.",
    ], size=13, space=6)
    takeaway(s, Inches(5.55),
             "Run PFPT/CAIS offline beside baseline RAG metrics. Never insert the audit "
             "into live alert dispatch.")

    # ------------------------------------------------------------ rag eval
    s = page(prs, "How this layer will be judged", "RAG explanation")
    table(s, MG, Inches(1.35), CWD, [
        ["Metric", "What it asks", "How it is measured"],
        ["Recall@k / MRR", "Is the right passage near the top?", "Hand-built question set"],
        ["Faithfulness", "Does the answer follow those passages?", "RAGAS / ARES + review"],
        ["Answer relevance", "Does it answer the question asked?", "RAGAS / RAGChecker"],
        ["Citation precision", "Does every claim trace to a supporting passage?",
         "ALCE-style check"],
        ["Refusal behaviour", "Out-of-scope refuse; in-scope false-refuse rate?",
         "Fixed protocol"],
        ["CACS (F/G/S)", "Do attributions hold under forecast perturbation?",
         "PFPT + CAIS pairs"],
    ], col_w=[Inches(2.5), Inches(5.3), Inches(4.3)], size=12, row_h=0.36)
    takeaway(s, Inches(5.15),
             "None measured yet. Targets are fixed before measurement so the layer cannot "
             "be scored by choosing a threshold after the fact.")

    # ------------------------------------------------------------ section 03
    divider(prs, "03", "The alert service",
            "How does a probability become a message that is still read in month twelve?",
            ["Levels from the calibration / budget curve",
             "Hysteresis, deduplication, stale-data guard",
             "Delivery judged on fatigue, not only accuracy"])

    # ------------------------------------------------------------ alerts pipeline
    s = page(prs, "End-to-end alert pipeline", "Alerting", title_size=26)
    pic(s, "fig_alerts_pipeline.png", MG + Inches(1.2), Inches(1.30), w=Inches(10.8))
    caption(s, MG, Inches(4.85), CWD,
            "Report Figure 6: Prediction to level to dedupe to deliver to log.")
    prose(s, MG, Inches(5.30), CWD, Inches(0.9), [
        f"Budget for half the events: {AE['b50']*100:.0f}% of ranked areas.  "
        f"Budget for 80%: {AE['b80']*100:.0f}%.  "
        f"Caught at a 6% budget: {AE['r6']*100:.0f}%.",
    ], size=13)
    takeaway(s, Inches(6.15),
             "Levels carry measured meaning because they come from the curve; "
             "deduplication stops a re-run from sending the same warning twice.")

    # ------------------------------------------------------------ alerts modular
    s = page(prs, "Rules core, ports and adapters", "Alerting", title_size=26)
    pic(s, "fig_alerts_modular.png", MG + Inches(2.4), Inches(1.25), w=Inches(8.4), h=Inches(4.7))
    caption(s, MG, Inches(6.10), CWD,
            "Report Figure 7: Modular alerting engine: core rules, four ports, replaceable adapters.")
    takeaway(s, Inches(6.50),
             "The core does not know SMS vendors or databases — adapters plug in from outside.",
             h=Inches(0.42))

    # ------------------------------------------------------------ conclusion
    s = page(prs, "What is built, and what a pilot would settle", "Conclusion",
             title_size=26)
    labeled(s, MG, Inches(1.40), Inches(5.95), Inches(2.5), "", "Conclusion",
            "The risk engine is built and measured: six families, two splits, calibrated, "
            "reproducible from committed scripts. RAG and alert layers are specified to "
            "their interfaces, rules and evaluation protocols (including PFPT/CAIS).",
            head_size=16)
    labeled(s, MG + Inches(6.15), Inches(1.40), Inches(5.95), Inches(2.5), "",
            "Future scope",
            "Model reporting capacity explicitly. Score baseline RAG metrics and the "
            "PFPT/CAIS attribution audit on locked fixtures. Pilot alerts with a district "
            "office and report precision, recall and fatigue.",
            head_size=16)
    prose(s, MG, Inches(4.20), CWD, Inches(1.2), [
        f"Dominant limitation: a negative may mean no disease or no report. With {POS} "
        "positives, uncertainty on every headline metric is wide.",
    ], size=14)
    takeaway(s, Inches(5.55),
             "The model is finished. Evidence that RAG and alerts behave in use is not; "
             "a pilot is how it arrives.")

    # ------------------------------------------------------------ Q&A
    s = page(prs, "Questions", "Q&A ownership", title_size=32)
    table(s, MG, Inches(1.55), CWD, [
        ["Topic", "Who answers"],
        ["Data panel, features, splits, ML results", "Yuvraj Singh"],
        ["RAG explanation, citations, PFPT/CAIS", "Shaktimayee Mohanty"],
        ["Alert rules, delivery, audit trail", "P. Shanmukh Vardhan"],
        ["Scope, limits, future work", "Any of us"],
    ], col_w=[Inches(7.5), Inches(4.6)], size=15, row_h=0.50)
    takeaway(s, Inches(5.20), "Thank you. We will take questions now.")

    # ------------------------------------------------------------ references
    s = page(prs, "References", title_size=28)
    refs = [
        "Lundberg & Lee (2017). A unified approach to interpreting model predictions. NeurIPS.",
        "Breiman (2001). Random forests. Machine Learning, 45(1).",
        "Chen & Guestrin (2016). XGBoost. KDD ’16.",
        "Ke et al. (2017). LightGBM. NeurIPS.",
        "Lewis et al. (2020). Retrieval-augmented generation. NeurIPS.",
        "Es et al. (2024). RAGAS. EACL System Demonstrations. arXiv:2309.15217.",
        "Saad-Falcon et al. (2024). ARES. NAACL. arXiv:2311.09476.",
        "Ru et al. (2024). RAGChecker. arXiv:2408.08067.",
        "Gao et al. (2023). ALCE: text with citations. EMNLP. arXiv:2305.14627.",
        "Robertson & Zaragoza (2009). BM25 and beyond. FnT IR.",
        "FAO (2024). FAOSTAT livestock stocks.",
        "World Bank (2024). World Development Indicators.",
        "NASA POWER (2024). Prediction of Worldwide Energy Resources.",
        "Europe PMC (2024). EMBL-EBI literature database.",
        "DAHD (2025). National Action Plan on Glanders. Government of India.",
        "ICAR-NIVEDI (2023). NADRES v2.",
    ]
    for i, r in enumerate(refs):
        tb = s.shapes.add_textbox(MG, Inches(1.22) + Inches(0.33) * i, CWD, Inches(0.32))
        tb.text_frame.word_wrap = True
        p = tb.text_frame.paragraphs[0]
        p.text = f"[{i+1}]  {r}"
        p.font.size = Pt(10); p.font.color.rgb = BODY; p.font.name = SANS

    prs.save(OUT)
    desk = pathlib.Path.home() / "Desktop" / "GlandersWatch_Deck.pptx"
    desk.write_bytes(OUT.read_bytes())
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(prs.slides)} slides)")
    print(f"copied {desk}")
    return OUT


if __name__ == "__main__":
    build()
