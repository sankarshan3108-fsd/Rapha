# RAPHA – Hospital Management System

*Technology organized around the art of healing.*

**Micro Project – 07: Hospital Patient Record System**
Industry focus: Healthcare  |  Integrated COs: CO2, CO3, CO4

A desktop application that keeps patient records in a **hash table** (direct access by ID), a **binary search tree** (ordered and range queries) and uses **merge sort** for the daily admission report. SQLite is used for permanent storage only.

## Team
| Name | Register No. |
|---|---|
| J Asher | URK25CS1035 |
| Priyadharshan N | URK25CS1028 |
| Sankar S | URK25CS1027 |

**Guided by:** Dr. J. A. M. Rexie, Assistant Professor
Division of Computer Science and Engineering, Karunya University

## Features
- Sidebar navigation, light/dark mode, live clock, toast notifications, status bar with the last operation and its comparison count.
- **Dashboard** – KPI cards, load-factor bar, admissions-per-day chart, department donut, recent admissions, quick actions.
- **All Patients** – BST in-order listing, search, department/gender filters, merge-sort column sorting, profile card, edit, delete.
- **Add / Edit Patient** – live validation, date picker, suggested free ID, insertion-result card (hash calculation, chain, BST path, rehash).
- **Lookup by ID** – animated hash calculation and chain walk.
- **Range Query** – pruned BST traversal with visited / included / pruned nodes.
- **Daily Report** – merge sort grouped by date, filters, merge-sort animation, export to .txt / .csv / .pdf.
- **Hash Table View** and **BST View** – interactive drawings, animated search path and traversals.
- **About Project** – brief, architecture diagram, complexity table, team.
- **Generate Report** – five PDF reports (daily admissions, department-wise, ID range, individual patient, complete hospital summary) with a text preview and optional DSA statistics; saved to `reports_output/`.
- **Algorithm Info panel** on every page with a live trace of the last operation.
- **Startup splash** (about 2 seconds) and a frosted-glass interface with a RAPHA logo.

## Screenshots
_Add screenshots here (Splash, Dashboard, Lookup, Range Query, Daily Report, Hash View, BST View, dark mode)._

## How to run (Windows)
```
cd hospital_records
pip install -r requirements.txt
python main.py
```
Run the tests: `python -m unittest discover -s tests -v`

Libraries: CustomTkinter, matplotlib, reportlab (PDF reports) and Pillow (Pillow is installed with CustomTkinter). Without Pillow the app still runs with a flat-colour version of the same design.

## Database (MySQL, with SQLite fallback)
MySQL stores the records (database `rapha_hospital`, table `patients`, see `schema.sql`). It is used for **storage only**: plain INSERT / UPDATE / DELETE and `SELECT *` at start-up. Lookup, range queries and sorting are done by the hash table, BST and merge sort.

1. Install MySQL Server (and optionally MySQL Workbench) and make sure the MySQL service is running.
2. `pip install -r requirements.txt`
3. Copy `db_config.example.ini` to `db_config.ini` and put your MySQL password in it (this file is git-ignored).
4. Copy the old records once: `python migrate_sqlite_to_mysql.py` (existing IDs are skipped; `patients.db` is kept as a backup).
5. `python main.py`

If MySQL cannot be reached the app explains why and offers to continue with the local SQLite file (`patients.db`); the status bar then shows an amber dot and "SQLite (offline mode)". With MySQL connected it shows a green dot and "MySQL connected · rapha_hospital".

## Folder structure
```
hospital_records/
  main.py               entry point (splash, DB, seed, load structures, GUI)
  patient.py  hash_table.py  bst.py  merge_sort.py
  database.py           SQLite + MySQL storage classes (same methods)
  db_setup.py  db_config.example.ini  schema.sql  migrate_sqlite_to_mysql.py
  patient_manager.py  seed_data.py
  algorithm_info.py     explanation text for the info panel
  reports/              report_generator.py (report data + PDF writer, uses reportlab)
  reports_output/       saved PDF reports (default save location)
  assets/               rapha.png, rapha.ico (generated with Pillow on first run)
  gui/
    app.py              window, sidebar, status bar, theme switching
    gui_theme.py        RAPHA colours, fonts, spacing (styling only)
    glass.py            frosted-glass backdrop and splash screen
    icons.py            line icons and the logo (Pillow)
    theme.py  widgets.py  utils.py
    pages/              dashboard, patients, add_patient, lookup, range_query,
                        report, hash_view, bst_view, about, generate_report
    visualizers/        hash_animation.py, bst_canvas.py, merge_sort_animation.py
  tests/                test_dsa.py, test_traces.py
```

## Architecture
```
GUI (CustomTkinter + Tkinter canvases)  ->  PatientManager  ->  Hash Table | BST | Merge Sort
                                                   |
                                             SQLite (patients.db, storage only)
```
At startup every row is loaded (`SELECT *`) into the hash table and, after a seeded shuffle (so the BST is not a linked list), into the BST. Every add/update/delete writes to SQLite and updates both structures.

## Time complexity
| Operation | Average | Worst | Space |
|---|---|---|---|
| Hash insert / search / delete | O(1) | O(n) | O(n) |
| Hash rehash | O(n) | O(n) | O(n) |
| BST insert / search / delete | O(log n) | O(n) skewed | O(n) |
| BST in-order traversal | O(n) | O(n) | O(h) |
| BST range query | O(h + k) | O(n) | O(h) |
| Merge sort | O(n log n) | O(n log n) | O(n) |
| Linear text search | O(n) | O(n) | O(1) |
