"""PatientManager: keeps SQLite, the hash table and the BST in sync."""
import random

from bst import BST
from hash_table import HashTable
from merge_sort import merge_sort, merge_sort_by


class PatientManager:
    def __init__(self, database):
        self.database = database
        self.hash_table = HashTable()
        self.bst = BST()
        self.last_add_info = None
        self.load_from_database()

    def load_from_database(self):
        """Fill both structures from SELECT * (done once at startup)."""
        patients = self.database.load_all()
        for patient in patients:
            self.hash_table.insert(patient.patient_id, patient)
        # SQLite returns rows in ascending ID order. Inserting sorted keys into
        # a BST makes it degenerate into a linked list (height n, O(n) ops).
        # Shuffling with a fixed seed gives a balanced-ish tree, repeatably.
        shuffled = list(patients)
        random.Random(42).shuffle(shuffled)
        for patient in shuffled:
            self.bst.insert(patient.patient_id, patient)

    # ---- write operations: DB first, then both structures ----
    def add_patient(self, patient):
        """Store a new patient. Returns the hash slot used.

        Also fills self.last_add_info (hash calculation, chain, BST path,
        rehash flag) so the GUI can show an "insertion result" card.
        """
        if self.hash_table.search(patient.patient_id) is not None:
            raise ValueError("Patient ID %d already exists." % patient.patient_id)
        table = self.hash_table
        size_before = table.size
        slot_before = table.hash(patient.patient_id)
        chain_before = table.get_slots()[slot_before]
        bst_path, parent_key, side = self.bst.insert_path(patient.patient_id)
        self.database.insert(patient)
        slot = self.hash_table.insert(patient.patient_id, patient)
        self.bst.insert(patient.patient_id, patient)
        self.last_add_info = {
            "id": patient.patient_id,
            "size_before": size_before,
            "slot_before": slot_before,
            "chain_before": list(chain_before),
            "slot": slot,
            "chain": table.get_slots()[slot],
            "rehashed": table.size != size_before,
            "size_after": table.size,
            "load_factor": table.load_factor(),
            "bst_path": bst_path,
            "bst_parent": parent_key,
            "bst_side": side,
        }
        return slot

    # ---- extras used by the GUI (traces and helpers) ----
    def lookup_trace(self, patient_id):
        """Hash lookup with explanation: (patient, slot, steps, size)."""
        patient, slot, steps = self.hash_table.search_trace(patient_id)
        return patient, slot, steps, self.hash_table.size

    def next_free_id(self):
        """Suggest max existing ID + 1, skipping any ID the hash table has."""
        highest = self.bst.max_key()
        candidate = 1001 if highest is None else highest + 1
        while self.hash_table.search(candidate) is not None:
            candidate += 1
        return candidate

    def sort_patients(self, patients, column, descending=False):
        """Sort a list of patients by column index (0..7) with merge sort.

        Returns (sorted_list, comparisons).  Text columns compare in lower case.
        """
        def key_func(patient):
            value = patient.as_row()[column]
            return value.lower() if isinstance(value, str) else value
        return merge_sort_by(patients, key_func, descending)

    def update_patient(self, patient):
        if self.hash_table.search(patient.patient_id) is None:
            raise ValueError("Patient ID %d does not exist." % patient.patient_id)
        self.database.update(patient)
        self.hash_table.update(patient.patient_id, patient)
        self.bst.insert(patient.patient_id, patient)   # overwrites value

    def delete_patient(self, patient_id):
        if self.hash_table.search(patient_id) is None:
            raise ValueError("Patient ID %d does not exist." % patient_id)
        self.database.delete(patient_id)
        self.hash_table.delete(patient_id)
        self.bst.delete(patient_id)

    # ---- read operations: only the DSA structures are used ----
    def get_patient(self, patient_id):
        return self.hash_table.search(patient_id)

    def all_patients(self):
        """Sorted by ID via BST in-order traversal."""
        return self.bst.inorder()

    def range_query(self, low, high):
        """Returns (patients, nodes_visited)."""
        result = self.bst.range_query(low, high)
        return result, self.bst.last_nodes_visited

    def daily_report(self):
        """Returns (patients sorted by date then ID, comparisons)."""
        return merge_sort(self.bst.inorder())

    def count(self):
        return self.hash_table.count
