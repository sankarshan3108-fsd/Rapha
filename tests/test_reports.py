import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import Database
from patient_manager import PatientManager
from reports import report_generator as rg
from seed_data import seed_if_empty

try:
    import reportlab  # noqa: F401
    HAVE_REPORTLAB = True
except ImportError:
    HAVE_REPORTLAB = False

LOGO = os.path.join(os.path.dirname(__file__), "..", "assets", "rapha.png")

CASES = [
    ("daily", {}),
    ("daily", {"date": "2026-10-22"}),
    ("daily", {"date": "1999-01-01"}),            # no admissions that day
    ("department", {}),
    ("department", {"department": "ENT"}),
    ("range", {"low": "1040", "high": "1060"}),
    ("range", {"low": "5", "high": "9"}),         # empty result
    ("patient", {"patient_id": "1045"}),
    ("summary", {}),
]


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.database = Database(":memory:")
        self.database.create_table()
        seed_if_empty(self.database)
        self.manager = PatientManager(self.database)
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        self.database.close()

    def test_every_type_builds_and_previews(self):
        for kind, options in CASES:
            for include in (True, False):
                report = rg.build_report(self.manager, kind, options, include)
                text = rg.preview_text(report)
                self.assertIn("RAPHA", text)
                self.assertIn(report["title"].upper(), text)
                self.assertEqual("DSA STATISTICS" in text, include and kind != "summary" or
                                 (kind == "summary" and include))

    @unittest.skipUnless(HAVE_REPORTLAB, "reportlab not installed")
    def test_every_type_writes_a_pdf(self):
        for kind, options in CASES:
            report = rg.build_report(self.manager, kind, options, True)
            path = os.path.join(self.folder, rg.suggested_filename(report))
            rg.write_pdf(report, path, LOGO)
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(5), b"%PDF-")
            self.assertGreater(os.path.getsize(path), 2000)

    def test_daily_is_date_ordered_with_counts(self):
        report = rg.build_report(self.manager, "daily", {}, True)
        headings = [b["text"] for b in report["blocks"] if b["type"] == "heading"]
        dates = [h.split()[0] for h in headings]
        self.assertEqual(dates, ["2026-10-21", "2026-10-22", "2026-10-23", "2026-10-24", "2026-10-25"])
        self.assertTrue(all("6 admissions" in h for h in headings))
        stats = [b for b in report["blocks"] if b["type"] == "stats"][0]
        self.assertEqual(dict(stats["items"])["Merge sort comparisons"],
                         self.manager.daily_report()[1])

    def test_range_uses_bst_and_reports_pruning(self):
        report = rg.build_report(self.manager, "range", {"low": "1040", "high": "1060"}, True)
        table = [b for b in report["blocks"] if b["type"] == "table"][0]
        ids = [int(row[0]) for row in table["rows"]]
        self.assertEqual(ids, [1041, 1045, 1049, 1052, 1057])
        stats = dict([b for b in report["blocks"] if b["type"] == "stats"][0]["items"])
        self.assertEqual(stats["Results found"], 5)
        self.assertEqual(stats["Nodes visited"] + stats["Nodes pruned (skipped)"], 30)

    def test_department_groups_are_in_id_order(self):
        report = rg.build_report(self.manager, "department", {}, False)
        for block in report["blocks"]:
            if block["type"] == "table" and block["headers"][0] == "ID":
                ids = [int(row[0]) for row in block["rows"]]
                self.assertTrue(all(a < b for a, b in zip(ids, ids[1:])))

    def test_individual_patient_statistics(self):
        report = rg.build_report(self.manager, "patient", {"patient_id": "1045"}, True)
        stats = dict([b for b in report["blocks"] if b["type"] == "stats"][0]["items"])
        self.assertEqual(stats["Hash calculation"], "1045 % 67 = 40")
        self.assertEqual(stats["Hash slot"], 40)

    def test_bad_input_gives_friendly_errors(self):
        with self.assertRaises(rg.ReportError):
            rg.build_report(self.manager, "patient", {"patient_id": "9999"})
        with self.assertRaises(rg.ReportError):
            rg.build_report(self.manager, "patient", {"patient_id": "abc"})
        with self.assertRaises(rg.ReportError):
            rg.build_report(self.manager, "range", {"low": "50", "high": "10"})
        with self.assertRaises(rg.ReportError):
            rg.build_report(self.manager, "range", {"low": "", "high": "10"})

    def test_summary_ends_with_team_page(self):
        report = rg.build_report(self.manager, "summary", {}, True)
        text = rg.preview_text(report)
        for needle in ("J Asher", "URK25CS1035", "Sankar S", "Dr. J. A. M. Rexie",
                       "Data Structure Status"):
            self.assertIn(needle, text)

    def test_file_name_pattern(self):
        import datetime
        report = rg.build_report(self.manager, "daily", {}, True,
                                 now=datetime.datetime(2026, 10, 25, 14, 30))
        self.assertEqual(rg.suggested_filename(report), "RAPHA_Daily_Admissions_2026-10-25_1430.pdf")


if __name__ == "__main__":
    unittest.main()
