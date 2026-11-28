"""Build the Hito 2 report (.docx) using the Hito 1 .docx as visual template.

Content source: informe_oficial.md. Layout/styles: Informe_Hito_1_*.docx.
Usage: python build_informe_hito2.py
"""
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape

import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "Informe_Hito_1_Consolidacion_Harness_Ley_21719.docx")
SOURCE = os.path.join(HERE, "informe_oficial.md")
OUTPUT = os.environ.get("INFORME_OUT") or os.path.join(HERE, "Informe_Hito_2_Verificacion_Privacidad_Ley_21719.docx")

REPO_URL = "https://github.com/Cliptap/compliance-graph-harness"
SOFFICE = os.environ.get("SOFFICE") or shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
NAVY, BLUE, TEXT, GRAY = "1A365D", "2B6CB0", "2D3748", "4A5568"
W = nsdecls("w", "r")

doc = docx.Document(TEMPLATE)
body = doc.element.body
sect = body.find(qn("w:sectPr"))


def add(xml):
    el = parse_xml(xml)
    sect.addprevious(el)
    return el


# --------------------------------------------------------------------------- inline
HYPERLINK_RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
TOKEN = re.compile(r"(`[^`]+`|\[[^\]]+\]\(https?://[^)\s]+\)|\*\*|\*)")


def rpr(bold=False, italic=False, code=False, color=None, size=None, underline=False):
    p = ""
    if code:
        p += '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>'
    elif color or size or bold or italic:
        p += '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>'
    if bold:
        p += "<w:b/>"
    if italic:
        p += "<w:i/>"
    if color:
        p += f'<w:color w:val="{color}"/>'
    if size:
        p += f'<w:sz w:val="{size}"/>'
    if underline:
        p += f'<w:u w:val="{underline if isinstance(underline, str) else "single"}"/>'
    return f"<w:rPr>{p}</w:rPr>" if p else ""


# Internal cross-references (Word bookmarks + anchored hyperlinks).
LINKS = {"refs": set(), "gloss": {}, "gloss_keys": {}, "gloss_active": True, "refs_active": True}
_bookmark_id = [100]


def bookmark(name, inner):
    _bookmark_id[0] += 1
    bid = _bookmark_id[0]
    return f'<w:bookmarkStart w:id="{bid}" w:name="{name}"/>{inner}<w:bookmarkEnd w:id="{bid}"/>'


def anchor_link(anchor, text, underline, **kw):
    return f'<w:hyperlink w:anchor="{anchor}" w:history="1">{run(text, underline=underline, **kw)}</w:hyperlink>'


CITATION = re.compile(r"\[(\d{1,2})\]")


def gloss_regex():
    keys = sorted(LINKS["gloss_keys"], key=len, reverse=True)
    if not keys or not LINKS["gloss_active"]:
        return None
    alt = "|".join(re.escape(k) for k in keys)
    return re.compile(rf"(?<![\w-])({alt})(?:es|s)?(?![\w-])", re.IGNORECASE)


def linked_text(text, links, **kw):
    if not links:
        return run(text, **kw)
    out = []
    while text:
        cit = CITATION.search(text) if LINKS["refs_active"] else None
        if cit and int(cit.group(1)) not in LINKS["refs"]:
            cit = None
        gr = gloss_regex()
        gl = gr.search(text) if gr else None
        m = min((x for x in (cit, gl) if x), key=lambda x: x.start(), default=None)
        if m is None:
            out.append(run(text, **kw))
            break
        out.append(run(text[: m.start()], **kw))
        if m is cit:
            out.append(anchor_link(f"ref_{cit.group(1)}", m.group(0), False, **{**kw, "color": BLUE}))
        else:
            anchor = LINKS["gloss_keys"][m.group(1).lower()]
            out.append(anchor_link(anchor, m.group(0), "dotted", **{**kw, "color": BLUE}))
            for k in [k for k, a in LINKS["gloss_keys"].items() if a == anchor]:
                del LINKS["gloss_keys"][k]
        text = text[m.end():]
    return "".join(out)


def run(text, **kw):
    if text == "":
        return ""
    return f'<w:r>{rpr(**kw)}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def inline(text, size=None, color=None, bold=False, italic=False, links=True):
    """Convert a markdown inline string to WordprocessingML runs."""
    text = text.replace("\\[", "[").replace("\\]", "]").replace("\\|", "|")
    out, b, i = [], bold, italic
    for part in TOKEN.split(text):
        if part == "":
            continue
        if part == "**":
            b = not b
        elif part == "*":
            i = not i
        elif part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(run(part[1:-1], code=True, bold=b, italic=i, color=color, size=(size - 1 if size else 20)))
        elif part.startswith("[") and "](" in part:
            label, url = re.match(r"\[([^\]]+)\]\((.+)\)", part).groups()
            rid = doc.part.relate_to(url, HYPERLINK_RT, is_external=True)
            out.append(
                f'<w:hyperlink r:id="{rid}" w:history="1">'
                f"{run(label, bold=b, italic=i, color=BLUE, size=size, underline=True)}</w:hyperlink>"
            )
        else:
            out.append(linked_text(part, links, bold=b, italic=i, color=color, size=size))
    return "".join(out)


# --------------------------------------------------------------------------- blocks
TOC_ENTRIES = []


def toc_mark(level, text, runs):
    name = f"_Toc{len(TOC_ENTRIES) + 1:04d}"
    TOC_ENTRIES.append((level, re.sub(r"[*`\\]", "", text), name))
    return bookmark(name, runs)


def h1(text):
    add(
        f'<w:p {W}><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>'
        f"{toc_mark(0, text, inline(text, size=32, color=NAVY, bold=True, links=False))}</w:p>"
    )


def h2(text):
    add(
        f'<w:p {W}><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="80"/><w:outlineLvl w:val="1"/></w:pPr>'
        f"{toc_mark(1, text, inline(text, size=26, color=BLUE, bold=True, links=False))}</w:p>"
    )


def h3(text):
    add(
        f'<w:p {W}><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="60"/><w:outlineLvl w:val="2"/></w:pPr>'
        f"{inline(text, size=23, color=GRAY, bold=True, links=False)}</w:p>"
    )


def para(text):
    add(f"<w:p {W}>{inline(text)}</w:p>")


def spacer():
    add(f'<w:p {W}><w:pPr><w:spacing w:before="0" w:after="80"/></w:pPr></w:p>')


def list_item(marker, text, level=0, numbered=False, mark=None):
    left = 567 + 340 * level
    prefix = run(marker, bold=True, color=NAVY) if numbered else run(marker, color=BLUE, bold=True)
    if mark:
        prefix = bookmark(mark, prefix)
    add(
        f'<w:p {W}><w:pPr><w:spacing w:after="60"/><w:ind w:left="{left}" w:hanging="283"/></w:pPr>'
        f"{prefix}<w:r><w:tab/></w:r>{inline(text)}</w:p>"
    )


def callout(label, text_paragraphs, fill="F7FAFC", bar=BLUE):
    paras = []
    for k, t in enumerate(text_paragraphs):
        head = ""
        if k == 0 and label:
            head = f'<w:r>{rpr(bold=True, color=NAVY, size=21)}<w:t>{escape(label)}</w:t><w:br/></w:r>'
        paras.append(
            f'<w:p><w:pPr><w:spacing w:line="276" w:lineRule="auto" w:after="40"/></w:pPr>{head}'
            f"{inline(t, size=20, color=TEXT, italic=True)}</w:p>"
        )
    add(
        f'<w:tbl {W}><w:tblPr><w:tblW w:type="auto" w:w="0"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/></w:tblPr>'
        f'<w:tblGrid><w:gridCol w:w="9360"/></w:tblGrid><w:tr><w:tc><w:tcPr><w:tcW w:type="dxa" w:w="9360"/>'
        f'<w:shd w:fill="{fill}"/><w:tcMar><w:top w:w="140" w:type="dxa"/><w:bottom w:w="140" w:type="dxa"/>'
        f'<w:left w:w="200" w:type="dxa"/><w:right w:w="200" w:type="dxa"/></w:tcMar><w:tcBorders><w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{bar}"/><w:bottom w:val="none"/><w:right w:val="none"/>'
        f'</w:tcBorders></w:tcPr>{"".join(paras)}</w:tc></w:tr></w:tbl>'
    )
    spacer()


def code_block(lines):
    runs = []
    for n, ln in enumerate(lines):
        if n:
            runs.append("<w:r><w:br/></w:r>")
        runs.append(run(ln, code=True, color=TEXT, size=18))
    add(
        f'<w:tbl {W}><w:tblPr><w:tblW w:type="auto" w:w="0"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/></w:tblPr>'
        f'<w:tblGrid><w:gridCol w:w="9360"/></w:tblGrid><w:tr><w:tc><w:tcPr><w:tcW w:type="dxa" w:w="9360"/>'
        f'<w:shd w:fill="F7FAFC"/><w:tcMar><w:top w:w="120" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/>'
        f'<w:left w:w="180" w:type="dxa"/><w:right w:w="180" w:type="dxa"/></w:tcMar><w:tcBorders>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/><w:left w:val="single" w:sz="16" w:space="0" w:color="A0AEC0"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/><w:right w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/>'
        f'</w:tcBorders></w:tcPr><w:p><w:pPr><w:spacing w:line="252" w:lineRule="auto" w:after="0"/></w:pPr>'
        f'{"".join(runs)}</w:p></w:tc></w:tr></w:tbl>'
    )
    spacer()


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def table(rows, aligns):
    ncols = len(rows[0])
    for r in rows:
        assert len(r) == ncols, f"column mismatch: {r}"
    plain = lambda s: re.sub(r"[*`\\]", "", s)
    weights = []
    for c in range(ncols):
        longest = max(len(plain(r[c])) for r in rows[1:]) if len(rows) > 1 else 10
        head = len(plain(rows[0][c]))
        weights.append(min(max(longest, head * 0.8, 7), 58) ** 0.85)
    total = sum(weights)
    dense = ncols >= 8
    per_char = 78 if dense else 88
    minw = []
    for c in range(ncols):
        words = [w for r in rows for w in plain(r[c]).split()]
        longest_word = min(max((len(w) for w in words), default=4), 18)
        short_cells = [len(plain(r[c])) for r in rows[1:] if len(plain(r[c])) <= 9]
        longest_word = max(longest_word, max(short_cells, default=0))
        is_code = sum(r[c].startswith("`") for r in rows[1:]) >= max(1, len(rows) // 2)
        pc = per_char + 18 if is_code else per_char
        minw.append(longest_word * pc + 260)
    widths = [max(int(9360 * w / total), m) for w, m in zip(weights, minw)]
    excess = sum(widths) - 9360
    if excess > 0:
        surplus = [max(w - m, 0) for w, m in zip(widths, minw)]
        tot_s = sum(surplus) or 1
        widths = [w - int(excess * s / tot_s) for w, s in zip(widths, surplus)]
    widths[-1] += 9360 - sum(widths)
    hs, bs = (16 if dense else 19), (16 if dense else 18)
    jc = {"l": "left", "c": "center", "r": "right"}
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)

    def cell(text, c, header, stripe):
        fill = NAVY if header else ("F7FAFC" if stripe else "FFFFFF")
        mar = (100, 100) if header else (80, 80)
        al = jc["l"] if header else jc[aligns[c]]
        if header:
            content = inline(text, size=hs, color="FFFFFF", bold=True)
            spacing = '<w:spacing w:after="0"/>'
            valign = ""
        else:
            content = inline(text, size=bs, color=TEXT)
            spacing = '<w:spacing w:after="0" w:line="264" w:lineRule="auto"/>'
            valign = '<w:vAlign w:val="center"/>'
        return (
            f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{widths[c]}"/><w:shd w:fill="{fill}"/>'
            f'<w:tcMar><w:top w:w="{mar[0]}" w:type="dxa"/><w:bottom w:w="{mar[1]}" w:type="dxa"/>'
            f'<w:left w:w="120" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tcMar>{valign}</w:tcPr>'
            f'<w:p><w:pPr>{spacing}<w:jc w:val="{al}"/></w:pPr>{content}</w:p></w:tc>'
        )

    trs = []
    for ri, r in enumerate(rows):
        hdr = ri == 0
        trpr = "<w:trPr><w:cantSplit/>" + ("<w:tblHeader/>" if hdr else "") + "</w:trPr>"
        trs.append("<w:tr>" + trpr + "".join(cell(t, c, hdr, ri % 2 == 0) for c, t in enumerate(r)) + "</w:tr>")
    add(
        f'<w:tbl {W}><w:tblPr><w:tblW w:type="auto" w:w="0"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
        f'<w:tblLook w:firstColumn="1" w:firstRow="1" w:lastColumn="0" w:lastRow="0" w:noHBand="0" w:noVBand="1" w:val="04A0"/>'
        f'<w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E0"/><w:left w:val="none"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E0"/><w:right w:val="none"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CBD5E0"/><w:insideV w:val="none"/></w:tblBorders></w:tblPr>'
        f"<w:tblGrid>{grid}</w:tblGrid>{''.join(trs)}</w:tbl>"
    )
    spacer()


# --------------------------------------------------------------------------- architecture figure
def architecture_figure(path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig, ax = plt.subplots(figsize=(11.2, 8.0))
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 8.2)
    ax.axis("off")
    BW, BH = 2.4, 0.9
    boxes = {
        "DEV": (1.4, 3.5, "Desarrollador\nintención y aprobación", "#1A365D", "white"),
        "AGENT": (4.2, 3.5, "Agente de programación", "#2B6CB0", "white"),
        "CHANGE": (7.0, 3.5, "Cambios en el repositorio", "#EDF2F7", "#1A365D"),
        "GATE": (9.8, 3.5, "Compuerta\nCLI / pre-commit", "#1A365D", "white"),
        "RULES": (2.4, 5.6, "Reglas y\n12 procedimientos", "#F7FAFC", "#2D3748"),
        "GRAPH": (4.8, 5.6, "Grafo estructural\ny linaje, BFS k ≤ 2", "#F7FAFC", "#2D3748"),
        "REVIEW": (7.3, 5.6, "Corrección supervisada", "#EDF2F7", "#1A365D"),
        "POLICY": (9.8, 5.6, "PolicyEngine +\nCatalogEngine", "#EDF2F7", "#1A365D"),
        "CATALOG": (9.8, 7.3, "Catálogo de 37 controles", "#F7FAFC", "#2D3748"),
        "STORE": (7.0, 7.3, "SQLite\nestructuras y hallazgos", "#F7FAFC", "#2D3748"),
        "TESTS": (9.8, 1.5, "Pruebas funcionales\ny regresión", "#EDF2F7", "#1A365D"),
        "CI": (5.8, 1.5, "CLI de evidencia\nintegración CI por configurar", "#F7FAFC", "#2D3748"),
        "EVID": (2.6, 1.5, "Manifiesto de evidencia\ndocumental", "#F7FAFC", "#2D3748"),
    }
    narrow = {"RULES", "GRAPH"}
    for key, (x, y, label, fc, tc) in boxes.items():
        bw = 2.0 if key in narrow else BW
        ax.add_patch(
            FancyBboxPatch((x - bw / 2, y - BH / 2), bw, BH, boxstyle="round,pad=0.02,rounding_size=0.12",
                           fc=fc, ec="#1A365D", lw=1.2)
        )
        ax.text(x, y, label, ha="center", va="center", fontsize=9.5, color=tc, fontweight="bold" if tc == "white" else "normal")

    def arrow(p, q, style="-", color="#1A365D", label=None, lpos=None, conn="arc3,rad=0"):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, lw=1.4, color=color,
                                     linestyle=style, connectionstyle=conn, shrinkA=0, shrinkB=0))
        if label:
            ax.text(*lpos, label, fontsize=8.5, color="#2D3748", ha="center", va="center",
                    bbox=dict(fc="white", ec="none", pad=1.2))

    arrow((2.6, 3.5), (3.0, 3.5))
    arrow((5.4, 3.5), (5.8, 3.5))
    arrow((8.2, 3.5), (8.6, 3.5))
    arrow((2.4, 5.15), (3.6, 3.95), "--", "#718096", "orientación", (2.7, 4.55))
    arrow((4.8, 5.15), (4.6, 3.95), "--", "#718096", "contexto", (4.95, 4.55))
    arrow((9.1, 3.95), (8.0, 5.15), "-", "#C53030", "hallazgos\nbloqueantes", (8.9, 4.65))
    arrow((7.0, 5.15), (7.0, 3.95), "-", "#C53030")
    arrow((9.8, 5.15), (9.8, 3.95))
    arrow((9.8, 6.85), (9.8, 6.05))
    arrow((8.2, 7.05), (8.8, 6.0), "-", "#1A365D")
    arrow((8.8, 6.05), (8.2, 7.1), "-", "#1A365D")
    arrow((9.8, 3.05), (9.8, 1.95), "-", "#2F855A", "resultado\naceptado", (9.8, 2.5))
    arrow((3.8, 1.5), (4.6, 1.5), "-")
    arrow((7.0, 1.5), (8.6, 1.5), "--", "#718096", "integración prevista", (7.8, 1.78))
    ax.plot([9.8, 9.8, 1.4, 1.4], [1.05, 0.35, 0.35, 3.0], color="#1A365D", lw=1.4)
    arrow((1.4, 2.5), (1.4, 3.05))
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# --------------------------------------------------------------------------- cover / header
def set_texts(el, values):
    ts = el.findall(".//" + qn("w:t"))
    assert len(ts) == len(values), (len(ts), values)
    for t, v in zip(ts, values):
        t.text = v


children = list(body)
set_texts(children[2], ["INFORME DE AVANCE — HITO 2:", "VERIFICACIÓN DE PRIVACIDAD, CALIBRACIÓN CIEGA Y COSTO"])
set_texts(
    children[3],
    [
        "Arnés de Supervisión de Software Asistido por IA mediante Grafos de Dependencias y Linaje de Datos bajo la Ley N° 21.719",
        "Caso de Estudio: Validación experimental de un arnés especializado en controles técnicos de privacidad sobre un banco sintético de comercio electrónico",
    ],
)
cover = children[4]
vals = {
    "Fecha de Entrega Hito 1:": ("Fecha de Entrega Hito 2:", "27 de noviembre de 2026"),
    "Estado del Incremento:": (
        None,
        "Verificación de privacidad, calibración ciega del detector y análisis de costo (Suite: 643 tests PASS)",
    ),
}
for tr in cover.findall(qn("w:tr")):
    cells = tr.findall(qn("w:tc"))
    label = "".join(t.text or "" for t in cells[0].iter(qn("w:t")))
    if label == "Integrantes:":
        ts = list(cells[1].iter(qn("w:t")))
        ts[1].text = "Bastian Oyanedel"
    if label == "Fecha de Corte / Actualización:":
        cover.remove(tr)
        continue
    if label == "Profesor Guía:":
        repo_row = copy.deepcopy(tr)
        rcells = repo_row.findall(qn("w:tc"))
        rcells[0].find(".//" + qn("w:t")).text = "Repositorio:"
        vrun = rcells[1].find(".//" + qn("w:r"))
        vrun.find(qn("w:t")).text = REPO_URL
        rid = doc.part.relate_to(REPO_URL, HYPERLINK_RT, is_external=True)
        link = parse_xml(f'<w:hyperlink {W} r:id="{rid}" w:history="1"/>')
        vrun.addprevious(link)
        link.append(vrun)
        vrun.find(qn("w:rPr")).find(qn("w:color")).set(qn("w:val"), BLUE)
        tr.addnext(repo_row)
    if label in vals:
        new_label, new_val = vals[label]
        if new_label:
            cells[0].find(".//" + qn("w:t")).text = new_label
        cells[1].find(".//" + qn("w:t")).text = new_val

# drop everything after the cover page break (index 5)
for el in children[6:]:
    if el is not sect:
        body.remove(el)

for s in doc.sections:
    for p in s.header.paragraphs:
        for r in p.runs:
            if "HITO 1" in r.text:
                r.text = "HITO 2: VERIFICACIÓN DE PRIVACIDAD, CALIBRACIÓN CIEGA Y COSTO (LEY N° 21.719)"

doc.core_properties.title = "Informe de Avance — Hito 2: Verificación de privacidad, calibración ciega y costo"
doc.core_properties.author = "Andrés Tapia; Bastian Oyanedel"

# --------------------------------------------------------------------------- markdown walk
lines = open(SOURCE, encoding="utf-8").read().splitlines()
start = next(i for i, l in enumerate(lines) if l.strip() == "### Resumen ejecutivo")
lines = lines[start + 1 :]


def gloss_anchor(term):
    slug = re.sub(r"[^a-z0-9]+", "_", term.lower().translate(str.maketrans("áéíóúñ", "aeioun"))).strip("_")
    return f"gl_{slug}"[:40]


def gloss_entry(text):
    m = re.match(r"\*\*(.+?):\*\*", text)
    if not m:
        return None, []
    term = m.group(1).replace("*", "")
    keys = [re.sub(r"\s*\(.*?\)", "", k).strip() for k in term.split(" / ")]
    return gloss_anchor(keys[0]), [k for k in keys if k]


section = None
for l in lines:
    if l.startswith("## "):
        section = "refs" if l.startswith("## 12.1") else "gloss" if l.startswith("## Anexo A") else None
    elif section == "refs" and re.match(r"^\d+\.\s", l):
        LINKS["refs"].add(int(l.split(".")[0]))
    elif section == "gloss" and l.startswith("- "):
        anchor, keys = gloss_entry(l[2:])
        for k in keys:
            LINKS["gloss_keys"][k.lower()] = anchor

EXTRA_ROW = (
    "| La lista completa de controles no estaba incluida en el informe. | "
    "Se incorpora el catálogo consolidado de 37 controles con identificador, base normativa y modo de verificación. | "
    "Sección 8.5 y Anexo D |"
)

def field(instr, placeholder, **kw):
    p = rpr(**kw)
    return (
        f'<w:r>{p}<w:fldChar w:fldCharType="begin"/></w:r>'
        f'<w:r>{p}<w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
        f'<w:r>{p}<w:fldChar w:fldCharType="separate"/></w:r>'
        f"{run(placeholder, **kw)}"
        f'<w:r>{p}<w:fldChar w:fldCharType="end"/></w:r>'
    )


# Table of contents: a Word TOC field built from the outline levels of the headings.
add(
    f'<w:p {W}><w:pPr><w:spacing w:before="360" w:after="200"/></w:pPr>'
    f'{run("ÍNDICE", bold=True, color=NAVY, size=32)}</w:p>'
)
toc_slot = add(f"<w:p {W}/>")
add(f'<w:p {W}><w:r><w:br w:type="page"/></w:r></w:p>')


def fill_toc(pages):
    """Write the TOC field result so Word never needs to update fields on open."""
    paras = []
    last = len(TOC_ENTRIES) - 1
    for k, (level, text, name) in enumerate(TOC_ENTRIES):
        top = level == 0
        kw = dict(size=21 if top else 20, color=NAVY if top else TEXT, bold=top)
        start = ""
        if k == 0:
            p = rpr(**kw)
            start = (f'<w:r>{p}<w:fldChar w:fldCharType="begin"/></w:r>'
                     f'<w:r>{p}<w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
                     f'<w:r>{p}<w:fldChar w:fldCharType="separate"/></w:r>')
        end = f'<w:r>{rpr(**kw)}<w:fldChar w:fldCharType="end"/></w:r>' if k == last else ""
        paras.append(parse_xml(
            f'<w:p {W}><w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9350"/></w:tabs>'
            f'<w:spacing w:before="{100 if top else 0}" w:after="40"/>'
            f'<w:ind w:left="{0 if top else 360}"/></w:pPr>{start}'
            f'<w:hyperlink w:anchor="{name}" w:history="1">{run(text, **kw)}'
            f'<w:r>{rpr(**kw)}<w:tab/></w:r>{run(str(pages.get(name, "")), **kw)}</w:hyperlink>{end}</w:p>'
        ))
    for p in paras:
        toc_slot.addprevious(p)
    body.remove(toc_slot)

for s in doc.sections:
    fp = s.footer.paragraphs[0]
    fp._p.append(parse_xml(
        f'<w:r {W}>{rpr(color="78909C", size=17)}<w:t xml:space="preserve">  ·  Página </w:t></w:r>'))
    for frag in parse_xml(f'<w:p {W}>{field("PAGE", "1", color="78909C", size=17)}</w:p>'):
        fp._p.append(frag)

h1("RESUMEN EJECUTIVO")
callout(
    "DECLARACIÓN DE ESTADO Y ALCANCE NORMATIVO",
    [
        "Estado del documento: segundo incremento funcional del arnés especializado en la Ley N° 21.719, con verificación "
        "de privacidad, calibración ciega del detector y análisis de costo. Las capacidades indicadas como propuestas, "
        "planificadas o futuras no forman parte de la implementación validada. Fecha de corte de la evidencia: "
        "27 de noviembre de 2026."
    ],
    fill="EDF2F7",
    bar=NAVY,
)

gloss_targets = set(LINKS["gloss_keys"].values())
i, n = 0, len(lines)
section = None
in_question_section = False
figure_done = False
while i < n:
    line = lines[i]
    s = line.strip()
    if not s:
        i += 1
        continue
    if s.startswith("```"):
        lang = s[3:].strip()
        j = i + 1
        block = []
        while not lines[j].strip().startswith("```"):
            block.append(lines[j])
            j += 1
        if lang == "mermaid":
            png = os.path.join(tempfile.gettempdir(), "arquitectura_hito2.png")
            architecture_figure(png)
            p = doc.add_paragraph()
            p.alignment = 1
            p.add_run().add_picture(png, width=Inches(6.4))
            cap = doc.add_paragraph()
            cap.alignment = 1
            cr = cap.add_run("Figura 1. Arquitectura del arnés y flujo de verificación.")
            cr.italic = True
            from docx.shared import Pt, RGBColor

            cr.font.size = Pt(9)
            cr.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)
            figure_done = True
        else:
            code_block(block)
        i = j + 1
        continue
    if s.startswith("# "):
        if s[2:].startswith("12."):
            LINKS["gloss_active"] = False
        h1(s[2:].strip())
        i += 1
        continue
    if s.startswith("## "):
        t = s[3:].strip()
        in_question_section = t.startswith("2.3")
        section = "refs" if t.startswith("12.1") else "gloss" if t.startswith("Anexo A") else None
        h2(t)
        i += 1
        continue
    if s.startswith("### "):
        h3(s[4:].strip())
        i += 1
        continue
    if s.startswith(">"):
        qs = []
        while i < n and lines[i].strip().startswith(">"):
            qs.append(lines[i].strip().lstrip(">").strip())
            i += 1
        label = "PREGUNTA CENTRAL DE INVESTIGACIÓN" if in_question_section else None
        callout(label, [" ".join(q for q in qs if q)])
        continue
    if s.startswith("|"):
        block = []
        while i < n and lines[i].strip().startswith("|"):
            block.append(lines[i])
            i += 1
        header = split_row(block[0])
        sep = split_row(block[1])
        aligns = ["c" if c.startswith(":") and c.endswith(":") else "r" if c.endswith(":") else "l" for c in sep]
        data = [header] + [split_row(b) for b in block[2:]]
        if header and header[0].startswith("Observación registrada"):
            data.insert(1, split_row(EXTRA_ROW))
        table(data, aligns)
        continue
    m = re.match(r"^(\s*)(?:(\d+)\.|[-*])\s+(.*)$", line)
    if m:
        indent = len(m.group(1))
        level = 1 if indent >= 2 else 0
        numbered = m.group(2) is not None
        marker = f"{m.group(2)}." if numbered else ("•" if level == 0 else "–")
        text = m.group(3)
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^\s*(?:\d+\.|[-*])\s+", lines[i]) \
                and not lines[i].strip().startswith(("|", "#", ">", "```")):
            text += " " + lines[i].strip()
            i += 1
        mark = None
        if section == "refs" and numbered:
            mark = f"ref_{m.group(2)}"
        elif section == "gloss" and level == 0:
            mark = gloss_entry(text)[0]
        list_item(marker, text, level, numbered, mark)
        continue
    buf = [s]
    i += 1
    while i < n and lines[i].strip() and not re.match(r"^\s*(?:\d+\.|[-*])\s+", lines[i]) \
            and not lines[i].strip().startswith(("|", "#", ">", "```")):
        buf.append(lines[i].strip())
        i += 1
    para(" ".join(buf))

assert figure_done
TOC_PAGES = os.environ.get("TOC_PAGES")
fill_toc(json.loads(TOC_PAGES) if TOC_PAGES else {})
settings = doc.settings.element
for el in settings.findall(qn("w:updateFields")):
    settings.remove(el)
xml = doc.element.xml
anchors = set(re.findall(r'w:anchor="([^"]+)"', xml))
marks = set(re.findall(r'w:bookmarkStart w:id="\d+" w:name="([^"]+)"', xml))
assert anchors <= marks, f"anchors without bookmark: {anchors - marks}"
print("citation links:", len(re.findall(r'w:anchor="ref_', xml)), "| glossary terms linked:",
      len(gloss_targets - set(LINKS["gloss_keys"].values())), "of", len(gloss_targets))
print("glossary terms never mentioned before the annexes:", sorted(set(LINKS["gloss_keys"].values())))


def heading_pages(path):
    """Render with LibreOffice and return the physical page of every TOC heading."""
    import pymupdf

    out = tempfile.mkdtemp()
    subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", out, path],
                   check=True, capture_output=True)
    pdf = pymupdf.open(os.path.join(out, os.path.splitext(os.path.basename(path))[0] + ".pdf"))
    texts = [re.sub(r"\s+", " ", p.get_text()).lower() for p in pdf]
    pdf.close()
    shutil.rmtree(out, ignore_errors=True)
    page = next(k for k, t in enumerate(texts) if "declaración de estado y alcance normativo" in t)
    pages = {}
    for _, text, name in TOC_ENTRIES:
        key = re.sub(r"\s+", " ", text).lower()[:45]
        found = next((k for k in range(page, len(texts)) if key in texts[k]), None)
        if found is None:
            print("TOC heading not found in render:", text)
        else:
            page = found
        pages[name] = page + 1
    return pages


if TOC_PAGES:
    doc.save(OUTPUT)
    print("saved", OUTPUT)
else:
    draft = os.path.join(tempfile.mkdtemp(), "toc_draft.docx")
    doc.save(draft)
    pages = heading_pages(draft)
    shutil.rmtree(os.path.dirname(draft), ignore_errors=True)
    subprocess.run([sys.executable, os.path.abspath(__file__)], check=True,
                   env={**os.environ, "TOC_PAGES": json.dumps(pages), "INFORME_OUT": OUTPUT})
