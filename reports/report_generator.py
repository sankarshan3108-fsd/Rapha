"""Report builder for RAPHA: collects report data from our own DSA code and
writes it as a PDF (reportlab) or as plain text (preview).

All data comes through PatientManager:
  * hash table   -> single-patient lookup (and its statistics)
  * BST          -> in-order traversal (ID order) and range queries
  * merge sort   -> ordering by admission date (and sorting names)
No SQL ordering/filtering and no sorted()/list.sort() is used here.

A report is first built as a neutral list of "blocks" (heading, table, ...).
The same blocks feed the text preview and the PDF, so they always agree.
"""
import datetime
import math
import os

from merge_sort import merge_sort_by, recursion_depth

BRAND_FULL = "RAPHA – Hospital Management System"
TAGLINE = "Technology organized around the art of healing."
FOOTER_TEXT = "Micro Project – 07: Hospital Patient Record System · Karunya University"
TEAM = [("J Asher", "URK25CS1035"), ("Priyadharshan N", "URK25CS1028"),
        ("Sankar S", "URK25CS1027")]
GUIDE = "Dr. J. A. M. Rexie, Assistant Professor"
DIVISION = "Division of Computer Science and Engineering, Karunya University"

TEAL = "#0B5E6E"
GREEN = "#2EAA4F"

KINDS = [
    ("daily", "Daily Admission Report"),
    ("department", "Department-wise Report"),
    ("range", "Patient ID Range Report"),
    ("patient", "Individual Patient Report"),
    ("summary", "Complete Hospital Summary"),
]
KIND_TITLES = dict(KINDS)

PATIENT_HEADERS = ["ID", "Name", "Age", "Gender", "Department", "Diagnosis", "Doctor", "Admitted"]
PATIENT_WIDTHS = [11, 27, 8, 13, 24, 26, 24, 18]
GROUPED_HEADERS = PATIENT_HEADERS[:-1]
GROUPED_WIDTHS = PATIENT_WIDTHS[:-1]


class ReportError(Exception):
    """A problem the user can fix (bad ID, bad range ...). Message is friendly."""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def n_log2_n(n):
    return round(n * math.log2(n)) if n > 1 else 0


def _plural(count, word):
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


def _rows(patients, with_date=True):
    rows = []
    for patient in patients:
        row = [str(value) for value in patient.as_row()]
        rows.append(row if with_date else row[:-1])
    return rows


def _table(headers, rows, widths, mono=(0,)):
    return {"type": "table", "headers": headers, "rows": rows, "widths": widths,
            "mono": list(mono)}


def _group_by(patients, key_func):
    """Group an ordered list: returns [(key, [patients])] in first-seen order.
    Uses parallel lists (no dict) and keeps the incoming order inside a group."""
    keys, groups = [], []
    for patient in patients:
        key = key_func(patient)
        if key in keys:
            groups[keys.index(key)].append(patient)
        else:
            keys.append(key)
            groups.append([patient])
    return list(zip(keys, groups))


def _algorithms(*items):
    return {"type": "algorithms", "items": list(items)}


def _stats(items):
    return {"type": "stats", "items": items}


def _int(text, label):
    text = str(text).strip()
    if not text.isdigit():
        raise ReportError("%s must be a whole number." % label)
    return int(text)


# ---------------------------------------------------------------------------
# building the report data
# ---------------------------------------------------------------------------
def build_report(manager, kind, options=None, include_dsa=True, now=None):
    """Return a report dict: kind, title, generated, name_part, blocks.

    options: date / department / low / high / patient_id depending on kind.
    Raises ReportError for input problems (e.g. unknown patient ID).
    """
    options = options or {}
    if kind not in KIND_TITLES:
        raise ReportError("Unknown report type.")
    report = {"kind": kind, "title": KIND_TITLES[kind],
              "generated": now or datetime.datetime.now(), "blocks": [],
              "name_part": ""}
    builder = {"daily": _daily, "department": _department, "range": _range,
               "patient": _patient, "summary": _summary}[kind]
    builder(manager, options, include_dsa, report)
    return report


def _daily(manager, options, include_dsa, report):
    ordered, comparisons = manager.daily_report()          # merge sort by date, then ID
    chosen = options.get("date") or "All dates"
    shown = [p for p in ordered if chosen == "All dates" or p.admission_date == chosen]
    groups = _group_by(shown, lambda p: p.admission_date)
    blocks = report["blocks"]
    report["name_part"] = "Daily_Admissions" + ("" if chosen == "All dates" else "_" + chosen)
    blocks.append({"type": "facts", "items": [
        ("Total patients", len(shown)), ("Admission dates", len(groups)),
        ("Date filter", chosen)]})
    if not shown:
        blocks.append({"type": "para", "text": "No admissions were found for the selected date."})
    for date, patients in groups:
        blocks.append({"type": "heading", "text": "%s  -  %s" % (date, _plural(len(patients), "admission"))})
        blocks.append(_table(GROUPED_HEADERS, _rows(patients, False), GROUPED_WIDTHS))
    if shown:
        blocks.append({"type": "para", "text": "Total admissions listed: %d" % len(shown)})
    if include_dsa:
        n = len(ordered)
        blocks.append(_stats([("Records sorted", n), ("Merge sort comparisons", comparisons),
                              ("n log2 n reference", n_log2_n(n)),
                              ("Recursion depth", recursion_depth(n))]))
        blocks.append(_algorithms(
            ("Merge sort (stable, divide and conquer)", "O(n log n) time, O(n) extra space"),
            ("Grouping the sorted list by date", "O(n)")))


def _department(manager, options, include_dsa, report):
    patients = manager.all_patients()                     # BST in-order = ID order
    chosen = options.get("department") or "All departments"
    groups = _group_by(patients, lambda p: p.department)
    names = [name for name, _ in groups]
    ordered_names, name_comparisons = merge_sort_by(names, lambda n: n.lower())
    blocks = report["blocks"]
    report["name_part"] = "Department_Report" + (
        "" if chosen == "All departments" else "_" + chosen.replace(" ", "-"))
    selected = [n for n in ordered_names if chosen == "All departments" or n == chosen]
    counts = [(n, len(groups[names.index(n)][1])) for n in selected]
    total = 0
    for _, count in counts:
        total += count
    blocks.append({"type": "facts", "items": [
        ("Total patients", total), ("Departments", len(selected)),
        ("Filter", chosen)]})
    if not selected:
        blocks.append({"type": "para", "text": "No patients were found for the selected department."})
    else:
        blocks.append({"type": "chart", "title": "Patients per department",
                       "labels": [n for n, _ in counts], "values": [c for _, c in counts]})
        blocks.append({"type": "heading", "text": "Summary"})
        blocks.append(_table(["Department", "Patients"], [[n, str(c)] for n, c in counts],
                             [70, 20], mono=(1,)))
    for name in selected:
        members = groups[names.index(name)][1]
        blocks.append({"type": "heading", "text": "%s  -  %s" % (name, _plural(len(members), "patient"))})
        blocks.append(_table(PATIENT_HEADERS, _rows(members), PATIENT_WIDTHS))
    if include_dsa:
        blocks.append(_stats([("Nodes visited by in-order traversal", len(patients)),
                              ("Departments sorted by name", len(names)),
                              ("Merge sort comparisons (names)", name_comparisons)]))
        blocks.append(_algorithms(
            ("BST in-order traversal (IDs ascending in every group)", "O(n)"),
            ("Merge sort on department names", "O(k log k) for k departments")))


def _range(manager, options, include_dsa, report):
    low = _int(options.get("low", ""), "Low ID")
    high = _int(options.get("high", ""), "High ID")
    if low > high:
        raise ReportError("Low ID must not be larger than High ID.")
    results, visited = manager.range_query(low, high)      # BST pruned in-order traversal
    total = manager.bst.size()
    blocks = report["blocks"]
    report["name_part"] = "ID_Range_%d-%d" % (low, high)
    blocks.append({"type": "facts", "items": [("ID range", "%d - %d" % (low, high)),
                                              ("Patients found", len(results))]})
    if results:
        blocks.append(_table(PATIENT_HEADERS, _rows(results), PATIENT_WIDTHS))
    else:
        blocks.append({"type": "para",
                       "text": "No patients have an ID between %d and %d." % (low, high)})
    if include_dsa:
        blocks.append(_stats([("Results found", len(results)), ("Nodes visited", visited),
                              ("Nodes pruned (skipped)", total - visited),
                              ("Total nodes in tree", total)]))
        blocks.append(_algorithms(
            ("BST range query (pruned in-order traversal)", "O(h + k), h = tree height, k = results")))


def _patient(manager, options, include_dsa, report):
    patient_id = _int(options.get("patient_id", ""), "Patient ID")
    patient, slot, steps, size = manager.lookup_trace(patient_id)   # hash table lookup
    if patient is None:
        raise ReportError("No patient with ID %d was found." % patient_id)
    report["name_part"] = "Patient_%d" % patient_id
    blocks = report["blocks"]
    blocks.append({"type": "facts", "items": [("Patient ID", patient.patient_id),
                                              ("Department", patient.department),
                                              ("Admitted", patient.admission_date)]})
    blocks.append({"type": "heading", "text": "Patient summary"})
    blocks.append({"type": "kv", "items": [
        ("Patient ID", str(patient.patient_id)), ("Name", patient.name),
        ("Age", str(patient.age)), ("Gender", patient.gender),
        ("Department", patient.department), ("Diagnosis", patient.diagnosis),
        ("Doctor", patient.doctor), ("Admission date", patient.admission_date)],
        "mono": ["Patient ID", "Age", "Admission date"]})
    if include_dsa:
        position = len(steps)
        blocks.append(_stats([
            ("Hash calculation", "%d %% %d = %d" % (patient_id, size, slot)),
            ("Hash slot", slot), ("Chain position", position),
            ("Comparisons", len(steps)),
            ("BST depth", manager.bst.depth_of(patient_id))]))
        blocks.append(_algorithms(
            ("Hash table lookup with separate chaining", "O(1) average, O(n) worst"),
            ("BST search (for depth)", "O(log n) average, O(n) skewed")))


def _summary(manager, options, include_dsa, report):
    patients = manager.all_patients()                      # BST in-order
    ordered, comparisons = manager.daily_report()          # merge sort
    table, tree = manager.hash_table, manager.bst
    report["name_part"] = "Hospital_Summary"
    blocks = report["blocks"]
    by_date = _group_by(ordered, lambda p: p.admission_date)
    by_dept = _group_by(patients, lambda p: p.department)
    names = [n for n, _ in by_dept]
    ordered_names, _ = merge_sort_by(names, lambda n: n.lower())
    blocks.append({"type": "facts", "items": [("Total patients", len(patients)),
                                              ("Departments", len(by_dept)),
                                              ("Admission dates", len(by_date))]})
    blocks.append({"type": "heading", "text": "Admissions per date"})
    blocks.append(_table(["Date", "Admissions"], [[d, str(len(g))] for d, g in by_date],
                         [70, 20], mono=(0, 1)))
    blocks.append({"type": "heading", "text": "Patients per department"})
    dept_counts = [(n, len(by_dept[names.index(n)][1])) for n in ordered_names]
    blocks.append({"type": "chart", "title": "Patients per department",
                   "labels": [n for n, _ in dept_counts], "values": [c for _, c in dept_counts]})
    blocks.append(_table(["Department", "Patients"], [[n, str(c)] for n, c in dept_counts],
                         [70, 20], mono=(1,)))
    blocks.append({"type": "heading", "text": "Patient list (ID order)"})
    blocks.append(_table(PATIENT_HEADERS, _rows(patients), PATIENT_WIDTHS))
    blocks.append({"type": "heading", "text": "Data Structure Status"})
    blocks.append({"type": "kv", "items": [
        ("Hash table size", str(table.size)), ("Records stored", str(table.count)),
        ("Load factor", "%.2f (limit 0.75)" % table.load_factor()),
        ("Collisions", str(table.collisions)),
        ("Longest chain", str(table.longest_chain())),
        ("Empty slots", str(table.empty_slots())),
        ("BST height", "%d (best possible %d)" % (
            tree.height(), math.ceil(math.log2(tree.size() + 1)) if tree.size() else 0)),
        ("BST nodes", str(tree.size())), ("BST leaves", str(tree.leaf_count())),
        ("Rehashes so far", str(table.rehash_count))],
        "mono": []})
    if include_dsa:
        blocks.append(_stats([("Merge sort comparisons", comparisons),
                              ("n log2 n reference", n_log2_n(len(ordered)))]))
        blocks.append(_algorithms(
            ("Hash table (separate chaining)", "O(1) average lookup"),
            ("Binary search tree", "O(log n) average; in-order list O(n); range O(h + k)"),
            ("Merge sort", "O(n log n) time, O(n) space")))
    blocks.append({"type": "pagebreak"})
    blocks.append({"type": "heading", "text": "Project details"})
    blocks.append({"type": "para", "text": "Micro Project – 07: Hospital Patient Record System"})
    blocks.append({"type": "para", "text": "Industry Focus: Healthcare   |   Integrated COs: CO2, CO3, CO4"})
    blocks.append({"type": "heading", "text": "Team members"})
    blocks.append(_table(["Name", "Register No."], [[n, r] for n, r in TEAM], [60, 40], mono=(1,)))
    blocks.append({"type": "para", "text": "Guided by: " + GUIDE})
    blocks.append({"type": "para", "text": DIVISION})


# ---------------------------------------------------------------------------
# file name and text preview
# ---------------------------------------------------------------------------
def suggested_filename(report):
    stamp = report["generated"].strftime("%Y-%m-%d_%H%M")
    return "RAPHA_%s_%s.pdf" % (report["name_part"], stamp)


def preview_text(report):
    """Plain-text rendering of the report blocks (shown in the Preview card)."""
    lines = [BRAND_FULL, TAGLINE, "", report["title"].upper(),
             "Generated: " + report["generated"].strftime("%d %b %Y, %H:%M"), "=" * 64]
    for block in report["blocks"]:
        kind = block["type"]
        if kind == "heading":
            lines += ["", block["text"], "-" * min(64, max(12, len(block["text"])))]
        elif kind == "para":
            lines.append(block["text"])
        elif kind == "facts":
            lines.append("   ".join("%s: %s" % (k, v) for k, v in block["items"]))
        elif kind == "table":
            widths = [min(24, max(len(h), *(len(r[i]) for r in block["rows"]) or [0]))
                      for i, h in enumerate(block["headers"])]
            fmt = lambda cells: "  ".join(str(c)[:w].ljust(w) for c, w in zip(cells, widths))
            lines.append(fmt(block["headers"]))
            lines.append("  ".join("-" * w for w in widths))
            lines += [fmt(r) for r in block["rows"]]
        elif kind == "kv":
            width = max(len(k) for k, _ in block["items"])
            lines += ["%s  %s" % (k.ljust(width), v) for k, v in block["items"]]
        elif kind == "chart":
            lines += ["", block["title"]]
            top = max(block["values"] or [1])
            for name, value in zip(block["labels"], block["values"]):
                lines.append("%-20s %s %d" % (name[:20], "#" * max(1, round(24 * value / top)), value))
        elif kind == "stats":
            lines += ["", "DSA STATISTICS"] + ["  %s: %s" % (k, v) for k, v in block["items"]]
        elif kind == "algorithms":
            lines += ["", "ALGORITHMS USED"] + ["  %s  -  %s" % (a, c) for a, c in block["items"]]
        elif kind == "pagebreak":
            lines += ["", "- - - - - - - - - - - - - - - - (new page) - - - -"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def write_pdf(report, path, logo_path=None):
    """Write the report as an A4 PDF.  Needs reportlab (ImportError if missing)."""
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.platypus import (HRFlowable, Image, KeepTogether, PageBreak, Paragraph,
                                    SimpleDocTemplate, Spacer, Table, TableStyle)

    teal, green = colors.HexColor(TEAL), colors.HexColor(GREEN)
    ink, muted = colors.HexColor("#1B2B2E"), colors.HexColor("#566B6E")
    border, band = colors.HexColor("#D5E1DE"), colors.HexColor("#F2F7F6")
    page_width, margin = A4[0], 18 * mm
    usable = page_width - 2 * margin

    def style(name, **kw):
        base = dict(fontName="Helvetica", fontSize=9, leading=12, textColor=ink, alignment=TA_LEFT)
        base.update(kw)
        return ParagraphStyle(name, **base)

    body = style("body")
    small = style("small", fontSize=8, leading=10)
    cell = style("cell", fontSize=8, leading=10)
    cell_mono = style("cellmono", fontName="Courier", fontSize=8, leading=10)
    head_cell = style("headcell", fontName="Helvetica-Bold", fontSize=8, leading=10,
                      textColor=colors.white)
    heading = style("heading", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                    textColor=teal, spaceBefore=12, spaceAfter=6)
    title_style = style("title", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=teal)
    brand_style = style("brand", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=ink)
    tag_style = style("tag", fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=muted)
    meta_style = style("meta", fontSize=8.5, leading=11, textColor=muted)

    def esc(text):
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    story = []
    # ---- header: logo + brand + tagline, rule, title, generated time
    logo = None
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, 14 * mm, 14 * mm)
    brand = [Paragraph(esc(BRAND_FULL), brand_style), Paragraph(esc(TAGLINE), tag_style)]
    header = Table([[logo or "", brand]], colWidths=[18 * mm, usable - 18 * mm])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                ("TOPPADDING", (0, 0), (-1, -1), 0)]))
    story += [header, Spacer(1, 6), HRFlowable(width="100%", thickness=1.2, color=green),
              Spacer(1, 8), Paragraph(esc(report["title"]), title_style),
              Paragraph("Generated: " + report["generated"].strftime("%d %B %Y, %H:%M"), meta_style),
              Spacer(1, 6)]

    def make_table(block):
        total = float(sum(block["widths"]))
        widths = [usable * w / total for w in block["widths"]]
        data = [[Paragraph(esc(h), head_cell) for h in block["headers"]]]
        for row in block["rows"]:
            data.append([Paragraph(esc(v), cell_mono if i in block["mono"] else cell)
                         for i, v in enumerate(row)])
        table = Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), teal),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, band]),
            ("GRID", (0, 0), (-1, -1), 0.4, border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]))
        return table

    def make_facts(block):
        cells = [[Paragraph("<font size=7 color='%s'>%s</font><br/><b>%s</b>" % (
            "#566B6E", esc(k).upper(), esc(v)), body) for k, v in block["items"]]]
        table = Table(cells, colWidths=[usable / len(block["items"])] * len(block["items"]))
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.4, border), ("INNERGRID", (0, 0), (-1, -1), 0.4, border),
            ("BACKGROUND", (0, 0), (-1, -1), band), ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("LINEABOVE", (0, 0), (-1, 0), 1.2, green)]))
        return table

    def make_kv(block):
        mono_labels = block.get("mono", [])
        items = block["items"]
        rows = []
        for i in range(0, len(items), 2):
            row = []
            for key, value in items[i:i + 2]:
                row += [Paragraph("<b>%s</b>" % esc(key), small),
                        Paragraph(esc(value), cell_mono if key in mono_labels else body)]
            while len(row) < 4:
                row += ["", ""]
            rows.append(row)
        table = Table(rows, colWidths=[usable * 0.17, usable * 0.33, usable * 0.17, usable * 0.33])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, border),
            ("BACKGROUND", (0, 0), (0, -1), band), ("BACKGROUND", (2, 0), (2, -1), band),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        return table

    def make_chart(block):
        drawing = Drawing(usable, 62 * mm)
        drawing.add(String(0, 62 * mm - 10, block["title"], fontName="Helvetica-Bold",
                           fontSize=9, fillColor=teal))
        values = block["values"]
        top = max(values or [1])
        chart = VerticalBarChart()
        chart.x, chart.y, chart.width, chart.height = 28, 24, usable - 44, 62 * mm - 44
        chart.data = [values]
        chart.categoryAxis.categoryNames = block["labels"]
        chart.categoryAxis.labels.fontName = "Helvetica"
        chart.categoryAxis.labels.fontSize = 7
        chart.categoryAxis.labels.dy = -2
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = top + 1
        chart.valueAxis.valueStep = max(1, math.ceil((top + 1) / 5.0))
        chart.valueAxis.labels.fontName = "Helvetica"
        chart.valueAxis.labels.fontSize = 7
        chart.valueAxis.gridStrokeColor = border
        chart.valueAxis.visibleGrid = True
        chart.bars[0].fillColor = teal
        chart.bars[0].strokeColor = None
        chart.barWidth = 12
        chart.barLabelFormat = "%d"
        chart.barLabels.fontName = "Helvetica-Bold"
        chart.barLabels.fontSize = 7
        chart.barLabels.nudge = 7
        drawing.add(chart)
        return drawing

    def make_box(title, lines):
        data = [[Paragraph("<b>%s</b>" % esc(title), style("boxt", textColor=teal, fontSize=9))]]
        data += [[Paragraph(line, small)] for line in lines]
        table = Table(data, colWidths=[usable])
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, green), ("BACKGROUND", (0, 0), (-1, -1), band),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        return table

    for block in report["blocks"]:
        kind = block["type"]
        if kind == "heading":
            story.append(Paragraph(esc(block["text"]), heading))
        elif kind == "para":
            story += [Paragraph(esc(block["text"]), body), Spacer(1, 4)]
        elif kind == "facts":
            story += [make_facts(block), Spacer(1, 4)]
        elif kind == "table":
            story += [make_table(block), Spacer(1, 4)]
        elif kind == "kv":
            story += [make_kv(block), Spacer(1, 4)]
        elif kind == "chart":
            story += [Spacer(1, 6), make_chart(block)]
        elif kind == "stats":
            story += [Spacer(1, 8), KeepTogether(make_box("DSA statistics", [
                "%s: <font name='Courier'>%s</font>" % (esc(k), esc(v)) for k, v in block["items"]]))]
        elif kind == "algorithms":
            story += [Spacer(1, 8), KeepTogether(make_box("Algorithms used", [
                "%s – %s" % (esc(a), esc(c)) for a, c in block["items"]]))]
        elif kind == "pagebreak":
            story.append(PageBreak())

    class NumberedCanvas(pdf_canvas.Canvas):
        """Canvas that knows the total page count so the footer can say 'Page X of Y'."""

        def __init__(self, *args, **kwargs):
            pdf_canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_pages = []

        def showPage(self):
            self._saved_pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._saved_pages)
            for state in self._saved_pages:
                self.__dict__.update(state)
                self._decorate(total)
                pdf_canvas.Canvas.showPage(self)
            pdf_canvas.Canvas.save(self)

        def _decorate(self, total):
            self.setStrokeColor(border)
            self.setLineWidth(0.5)
            self.line(margin, 14 * mm, page_width - margin, 14 * mm)
            self.setFont("Helvetica", 7.5)
            self.setFillColor(muted)
            self.drawString(margin, 10 * mm, FOOTER_TEXT)
            self.drawRightString(page_width - margin, 10 * mm,
                                 "Page %d of %d" % (self._pageNumber, total))
            if self._pageNumber > 1:        # slim running header on later pages
                self.setFillColor(teal)
                self.setFont("Helvetica-Bold", 8)
                self.drawString(margin, A4[1] - 11 * mm, BRAND_FULL)
                self.setStrokeColor(green)
                self.line(margin, A4[1] - 13 * mm, page_width - margin, A4[1] - 13 * mm)

    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=margin, rightMargin=margin,
                            topMargin=18 * mm, bottomMargin=20 * mm,
                            title="%s – %s" % (BRAND_FULL, report["title"]),
                            author="RAPHA")
    doc.build(story, canvasmaker=NumberedCanvas)
    return path
