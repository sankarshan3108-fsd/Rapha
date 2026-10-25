import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bst import BST
from database import Database
from hash_table import HashTable
from merge_sort import merge_sort
from patient import Patient
from patient_manager import PatientManager
from seed_data import SEED_ROWS, seed_if_empty


def make(pid, date="2026-10-21"):
    return Patient(pid, "P%d" % pid, 30, "Male", "ENT", "Flu", "Dr. X", date)


class HashTableTests(unittest.TestCase):
    def test_insert_and_search(self):
        table = HashTable()
        slot = table.insert(1045, "a")
        self.assertEqual(slot, 1045 % 31)
        self.assertEqual(table.search(1045), "a")
        self.assertIsNone(table.search(9999))

    def test_collisions_chain(self):
        table = HashTable()
        table.insert(5, "a")
        table.insert(36, "b")      # 36 % 31 == 5
        self.assertEqual(table.collisions, 1)
        self.assertEqual(table.get_slots()[5], [5, 36])
        self.assertEqual(table.search(36), "b")

    def test_rehash(self):
        table = HashTable()
        for key in range(1000, 1030):
            table.insert(key, key)
        self.assertGreater(table.size, 31)
        self.assertLessEqual(table.load_factor(), 0.75)
        for key in range(1000, 1030):
            self.assertEqual(table.search(key), key)

    def test_delete(self):
        table = HashTable()
        for key in (5, 36, 67):
            table.insert(key, key)
        self.assertTrue(table.delete(36))       # middle of chain
        self.assertTrue(table.delete(5))        # head
        self.assertFalse(table.delete(5))
        self.assertEqual(table.get_slots()[5], [67])
        self.assertEqual(table.count, 1)

    def test_update(self):
        table = HashTable()
        table.insert(1, "a")
        self.assertTrue(table.update(1, "b"))
        self.assertEqual(table.search(1), "b")
        self.assertFalse(table.update(2, "x"))


class BSTTests(unittest.TestCase):
    def build(self, keys):
        tree = BST()
        for key in keys:
            tree.insert(key, key)
        return tree

    def test_insert_search_path(self):
        tree = self.build([50, 30, 70, 20, 40])
        value, path = tree.search(40)
        self.assertEqual(value, 40)
        self.assertEqual(path, [50, 30, 40])
        self.assertIsNone(tree.search(99)[0])
        self.assertEqual(tree.size(), 5)
        self.assertEqual(tree.height(), 3)

    def test_inorder_sorted(self):
        keys = [50, 30, 70, 20, 40, 60, 80]
        self.assertEqual(self.build(keys).inorder(), sorted(keys))

    def test_delete_leaf(self):
        tree = self.build([50, 30, 70])
        self.assertTrue(tree.delete(30))
        self.assertEqual(tree.inorder(), [50, 70])

    def test_delete_one_child(self):
        tree = self.build([50, 30, 20])
        tree.delete(30)
        self.assertEqual(tree.inorder(), [20, 50])

    def test_delete_two_children(self):
        tree = self.build([50, 30, 70, 60, 80])
        tree.delete(50)
        self.assertEqual(tree.root.key, 60)
        self.assertEqual(tree.inorder(), [30, 60, 70, 80])
        self.assertEqual(tree.size(), 4)
        self.assertFalse(tree.delete(999))

    def test_range_query(self):
        tree = self.build([50, 30, 70, 20, 40, 60, 80])
        self.assertEqual(tree.range_query(35, 65), [40, 50, 60])
        self.assertLess(tree.last_nodes_visited, 7)   # pruning worked
        self.assertEqual(tree.range_query(100, 200), [])


class MergeSortTests(unittest.TestCase):
    def test_order(self):
        data = [make(3, "2026-10-22"), make(1, "2026-10-23"),
                make(2, "2026-10-21"), make(4, "2026-10-21")]
        result, comparisons = merge_sort(data)
        self.assertEqual([p.patient_id for p in result], [2, 4, 3, 1])
        self.assertGreater(comparisons, 0)
        self.assertEqual([p.patient_id for p in data], [3, 1, 2, 4])  # untouched

    def test_stability_by_id_tiebreak(self):
        data = [make(9), make(5), make(7)]
        result, _ = merge_sort(data)
        self.assertEqual([p.patient_id for p in result], [5, 7, 9])

    def test_empty_and_single(self):
        self.assertEqual(merge_sort([]), ([], 0))
        one = [make(1)]
        self.assertEqual(merge_sort(one), (one, 0))


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.database = Database(":memory:")
        self.database.create_table()
        seed_if_empty(self.database)
        self.manager = PatientManager(self.database)

    def test_load_and_seed(self):
        self.assertEqual(len(SEED_ROWS), 30)
        self.assertEqual(self.database.count(), 30)
        self.assertEqual(self.manager.hash_table.count, 30)
        self.assertEqual(self.manager.bst.size(), 30)
        ids = [p.patient_id for p in self.manager.all_patients()]
        self.assertEqual(ids, sorted(ids))
        self.assertLess(self.manager.bst.height(), 30)   # not degenerate

    def test_add_update_delete_stay_in_sync(self):
        self.manager.add_patient(make(1101))
        self.assertEqual(self.database.count(), 31)
        self.assertIsNotNone(self.manager.hash_table.search(1101))
        self.assertIsNotNone(self.manager.bst.search(1101)[0])
        with self.assertRaises(ValueError):
            self.manager.add_patient(make(1101))

        updated = make(1101)
        updated.name = "Changed"
        self.manager.update_patient(updated)
        self.assertEqual(self.manager.get_patient(1101).name, "Changed")
        self.assertEqual(self.manager.bst.search(1101)[0].name, "Changed")
        names = [p.name for p in self.database.load_all() if p.patient_id == 1101]
        self.assertEqual(names, ["Changed"])

        self.manager.delete_patient(1101)
        self.assertEqual(self.database.count(), 30)
        self.assertIsNone(self.manager.hash_table.search(1101))
        self.assertIsNone(self.manager.bst.search(1101)[0])


if __name__ == "__main__":
    unittest.main()
