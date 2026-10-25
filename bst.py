"""Binary Search Tree keyed by patient ID.

Rule: for every node, all IDs in the left subtree are smaller and all IDs in
the right subtree are larger.  This makes in-order traversal sorted.
"""


class BSTNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None


class BST:
    def __init__(self):
        self.root = None
        self._size = 0
        self.last_nodes_visited = 0   # set by range_query

    def insert(self, key, value):
        """Insert (or overwrite if key exists). Returns True if a new node.

        Start at root; go left if key < node, right if key > node; attach at
        the first empty spot.  O(log n) average, O(n) if skewed.
        """
        if self.root is None:
            self.root = BSTNode(key, value)
            self._size += 1
            return True
        current = self.root
        while True:
            if key == current.key:
                current.value = value
                return False
            if key < current.key:
                if current.left is None:
                    current.left = BSTNode(key, value)
                    break
                current = current.left
            else:
                if current.right is None:
                    current.right = BSTNode(key, value)
                    break
                current = current.right
        self._size += 1
        return True

    def search(self, key):
        """Return (value_or_None, path) where path = IDs of visited nodes.

        O(log n) average, O(n) skewed."""
        path = []
        current = self.root
        while current is not None:
            path.append(current.key)
            if key == current.key:
                return current.value, path
            current = current.left if key < current.key else current.right
        return None, path

    def delete(self, key):
        """Delete key; True if it existed.

        Cases: (1) leaf -> remove; (2) one child -> replace node by its child;
        (3) two children -> copy the in-order successor (smallest node of the
        right subtree) into this node, then delete that successor.
        O(log n) average, O(n) skewed.
        """
        self.root, removed = self._delete(self.root, key)
        if removed:
            self._size -= 1
        return removed

    def _delete(self, node, key):
        if node is None:
            return None, False
        if key < node.key:
            node.left, removed = self._delete(node.left, key)
            return node, removed
        if key > node.key:
            node.right, removed = self._delete(node.right, key)
            return node, removed
        # found the node to delete
        if node.left is None:          # leaf or only right child
            return node.right, True
        if node.right is None:         # only left child
            return node.left, True
        successor = node.right         # two children
        while successor.left is not None:
            successor = successor.left
        node.key, node.value = successor.key, successor.value
        node.right, _ = self._delete(node.right, successor.key)
        return node, True

    def inorder(self):
        """All values in ascending ID order (left, node, right). O(n)."""
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if node is None:
            return
        self._inorder(node.left, result)
        result.append(node.value)
        self._inorder(node.right, result)

    def range_query(self, low, high):
        """Values with low <= ID <= high, ascending.

        Pruned in-order traversal: visit the left subtree only if node.key >
        low (otherwise everything there is too small); visit the right subtree
        only if node.key < high.  Counts visited nodes in last_nodes_visited.
        O(h + k) where h = height, k = results.
        """
        result = []
        self.last_nodes_visited = 0
        self._range(self.root, low, high, result)
        return result

    def _range(self, node, low, high, result):
        if node is None:
            return
        self.last_nodes_visited += 1
        if node.key > low:
            self._range(node.left, low, high, result)
        if low <= node.key <= high:
            result.append(node.value)
        if node.key < high:
            self._range(node.right, low, high, result)

    def height(self):
        """Number of levels (empty tree = 0). O(n)."""
        return self._height(self.root)

    def _height(self, node):
        if node is None:
            return 0
        return 1 + max(self._height(node.left), self._height(node.right))

    def size(self):
        """Number of nodes. O(1)."""
        return self._size

    # ---- optional trace / statistics helpers (do not change the logic) ----
    def search_steps(self, key):
        """Explain a search: returns (found, steps).

        steps is a list of (node_key, text) such as '1120 > 1070 -> go right'.
        O(log n) average.
        """
        steps = []
        current = self.root
        while current is not None:
            if key == current.key:
                steps.append((current.key, "%d = %d -> found" % (key, current.key)))
                return True, steps
            if key < current.key:
                steps.append((current.key, "%d < %d -> go left" % (key, current.key)))
                current = current.left
            else:
                steps.append((current.key, "%d > %d -> go right" % (key, current.key)))
                current = current.right
        steps.append((None, "reached an empty spot -> not found"))
        return False, steps

    def insert_path(self, key):
        """Path an insert of key would take: (visited_keys, parent_key, side).

        Does NOT modify the tree - call it before insert(). O(h).
        """
        path = []
        current, parent, side = self.root, None, None
        while current is not None:
            path.append(current.key)
            if key == current.key:
                return path, parent, side
            parent = current
            if key < current.key:
                side, current = "left", current.left
            else:
                side, current = "right", current.right
        return path, parent.key if parent else None, side

    def range_trace(self, low, high):
        """Explain a range query without changing range_query().

        Returns (visited, included, pruned): lists of node keys.  'pruned'
        holds the root of every subtree that was skipped.  O(h + k).
        """
        visited, included, pruned = [], [], []
        self._range_trace(self.root, low, high, visited, included, pruned)
        return visited, included, pruned

    def _range_trace(self, node, low, high, visited, included, pruned):
        if node is None:
            return
        visited.append(node.key)
        if node.key > low:
            self._range_trace(node.left, low, high, visited, included, pruned)
        elif node.left is not None:
            pruned.append(node.left.key)
        if low <= node.key <= high:
            included.append(node.key)
        if node.key < high:
            self._range_trace(node.right, low, high, visited, included, pruned)
        elif node.right is not None:
            pruned.append(node.right.key)

    def preorder_keys(self):
        """Keys in Root, Left, Right order. O(n)."""
        result = []
        self._walk(self.root, result, "pre")
        return result

    def inorder_keys(self):
        """Keys in Left, Root, Right order (ascending). O(n)."""
        result = []
        self._walk(self.root, result, "in")
        return result

    def postorder_keys(self):
        """Keys in Left, Right, Root order. O(n)."""
        result = []
        self._walk(self.root, result, "post")
        return result

    def _walk(self, node, result, order):
        if node is None:
            return
        if order == "pre":
            result.append(node.key)
        self._walk(node.left, result, order)
        if order == "in":
            result.append(node.key)
        self._walk(node.right, result, order)
        if order == "post":
            result.append(node.key)

    def depth_of(self, key):
        """Depth of key (root = 0) or -1 if absent. O(h)."""
        value, path = self.search(key)
        if value is not None:
            return len(path) - 1
        return -1

    def leaf_count(self):
        """Number of nodes with no children. O(n)."""
        return self._leaves(self.root)

    def _leaves(self, node):
        if node is None:
            return 0
        if node.left is None and node.right is None:
            return 1
        return self._leaves(node.left) + self._leaves(node.right)

    def max_key(self):
        """Largest key (rightmost node) or None. O(h)."""
        current = self.root
        if current is None:
            return None
        while current.right is not None:
            current = current.right
        return current.key
