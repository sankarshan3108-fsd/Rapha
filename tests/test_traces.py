import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bst import BST
from database import Database
from hash_table import HashTable
from merge_sort import merge_sort_by, merge_sort_frames, recursion_depth
from patient import Patient
from patient_manager import PatientManager
from seed_data import seed_if_empty


class HashTraceTests(unittest.TestCase):
    def test_search_trace_counts_comparisons(self):
        table = HashTable()
        for key in (5, 36, 67):                 # all hash to slot 5
            table.insert(key, key)
        value, slot, steps = table.search_trace(67)
        self.assertEqual((value, slot), (67, 5))
        self.assertEqual(steps, [(5, False), (36, False), (67, True)])
        self.assertEqual(table.chain_position(36), (5, 2))
        self.assertEqual(table.chain_position(999), (999 % 31, 0))

    def test_stats_and_rehash_count(self):
        table = HashTable()
        for key in (5, 36):
            table.insert(key, key)
        self.assertEqual(table.longest_chain(), 2)
        self.assertEqual(table.empty_slots(), 30)
        for key in range(100, 130):
            table.insert(key, key)
        self.assertGreaterEqual(table.rehash_count, 1)


class BSTTraceTests(unittest.TestCase):
    def setUp(self):
        self.tree = BST()
        for key in (50, 30, 70, 20, 40, 60, 80):
            self.tree.insert(key, key)

    def test_search_steps(self):
        found, steps = self.tree.search_steps(60)
        self.assertTrue(found)
        self.assertEqual([k for k, _ in steps], [50, 70, 60])
        self.assertIn("go right", steps[0][1])
        found, steps = self.tree.search_steps(65)
        self.assertFalse(found)

    def test_insert_path_does_not_modify(self):
        path, parent, side = self.tree.insert_path(65)
        self.assertEqual((path, parent, side), ([50, 70, 60], 60, "right"))
        self.assertEqual(self.tree.size(), 7)

    def test_range_trace_matches_range_query(self):
        visited, included, pruned = self.tree.range_trace(35, 65)
        self.assertEqual(included, self.tree.range_query(35, 65))
        self.assertEqual(len(visited), self.tree.last_nodes_visited)
        self.assertIn(20, pruned)      # left child of 30 is skipped

    def test_traversals_and_stats(self):
        self.assertEqual(self.tree.preorder_keys(), [50, 30, 20, 40, 70, 60, 80])
        self.assertEqual(self.tree.inorder_keys(), [20, 30, 40, 50, 60, 70, 80])
        self.assertEqual(self.tree.postorder_keys(), [20, 40, 30, 60, 80, 70, 50])
        self.assertEqual(self.tree.leaf_count(), 4)
        self.assertEqual(self.tree.max_key(), 80)
        self.assertEqual(self.tree.depth_of(40), 2)
        self.assertEqual(self.tree.depth_of(99), -1)


class MergeSortExtraTests(unittest.TestCase):
    def test_sort_by_and_descending_stable(self):
        data = [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
        asc, comparisons = merge_sort_by(data, lambda x: x[0])
        self.assertEqual(asc, [(1, "b"), (1, "d"), (2, "a"), (2, "c")])
        self.assertGreater(comparisons, 0)
        desc, _ = merge_sort_by(data, lambda x: x[0], descending=True)
        self.assertEqual(desc, [(2, "a"), (2, "c"), (1, "b"), (1, "d")])

    def test_frames(self):
        class P:                      # minimal stand-in with the sort fields
            def __init__(self, d, i):
                self.admission_date, self.patient_id = d, i
        items = [P("b", 1), P("a", 2), P("c", 3), P("a", 1), P("b", 2)]
        frames = merge_sort_frames(items)
        self.assertEqual(frames[0][0], "divide")
        self.assertEqual(frames[-1][0], "merge")
        final = [(p.admission_date, p.patient_id) for p in frames[-1][2][0]]
        self.assertEqual(final, [("a", 1), ("a", 2), ("b", 1), ("b", 2), ("c", 3)])
        self.assertEqual(recursion_depth(5), 3)
        self.assertEqual(recursion_depth(1), 0)


class ManagerTraceTests(unittest.TestCase):
    def setUp(self):
        self.database = Database(":memory:")
        self.database.create_table()
        seed_if_empty(self.database)
        self.manager = PatientManager(self.database)

    def test_add_info_and_next_id(self):
        new_id = self.manager.next_free_id()
        self.assertEqual(new_id, 1101)
        patient = Patient(new_id, "T", 20, "Male", "ENT", "x", "y", "2026-10-25")
        slot = self.manager.add_patient(patient)
        info = self.manager.last_add_info
        self.assertEqual(info["slot"], slot)
        self.assertEqual(info["bst_path"][0], self.manager.bst.root.key)
        self.assertIn(info["bst_side"], ("left", "right"))
        self.assertEqual(self.manager.next_free_id(), 1102)

    def test_lookup_trace(self):
        patient, slot, steps, size = self.manager.lookup_trace(1045)
        self.assertEqual(patient.patient_id, 1045)
        self.assertEqual(slot, 1045 % size)
        self.assertTrue(steps[-1][1])

    def test_sort_patients(self):
        patients = self.manager.all_patients()
        result, _ = self.manager.sort_patients(patients, 2)       # by age
        ages = [p.age for p in result]
        self.assertTrue(all(ages[i] <= ages[i + 1] for i in range(len(ages) - 1)))


if __name__ == "__main__":
    unittest.main()
