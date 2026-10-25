"""Hash table with separate chaining (hand-written, no dict).

Idea: an array of "slots". A key goes to slot  id % size.  If two keys land in
the same slot (a collision) they are kept together in a linked list (chain).
"""


class Node:
    """One link in a slot's chain."""

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


def _is_prime(number):
    if number < 2:
        return False
    divisor = 2
    while divisor * divisor <= number:
        if number % divisor == 0:
            return False
        divisor += 1
    return True


def next_prime(number):
    """Smallest prime strictly greater than number."""
    candidate = number + 1
    while not _is_prime(candidate):
        candidate += 1
    return candidate


class HashTable:
    """Separate-chaining hash table keyed by integer patient ID."""

    INITIAL_SIZE = 31
    MAX_LOAD_FACTOR = 0.75

    def __init__(self, size=INITIAL_SIZE):
        self.size = size
        self.slots = [None] * size   # each entry is the head Node of a chain
        self.count = 0
        self.collisions = 0          # inserts that landed on a non-empty slot
        self.rehash_count = 0        # how many times the table has grown

    def hash(self, key):
        """Hash function h(id) = id % size.  O(1)."""
        return key % self.size

    def load_factor(self):
        """records / slots.  O(1)."""
        return self.count / self.size

    def insert(self, key, value):
        """Insert key->value and return the slot index used.

        Steps: compute slot; walk chain - if key already present, replace the
        value; otherwise add a new node at the end (counting a collision if the
        slot was not empty). Rehash afterwards if load factor > 0.75.
        Time: O(1) average, O(n) worst (all keys in one chain).
        """
        index = self.hash(key)
        current = self.slots[index]
        if current is None:
            self.slots[index] = Node(key, value)
        else:
            last = None
            while current is not None:
                if current.key == key:
                    current.value = value     # duplicate key: overwrite
                    return index
                last = current
                current = current.next
            last.next = Node(key, value)
            self.collisions += 1
        self.count += 1
        if self.load_factor() > self.MAX_LOAD_FACTOR:
            self._rehash()
            index = self.hash(key)            # slot changes after resize
        return index

    def search(self, key):
        """Return the value for key, or None.  O(1) average, O(n) worst."""
        current = self.slots[self.hash(key)]
        while current is not None:
            if current.key == key:
                return current.value
            current = current.next
        return None

    def update(self, key, value):
        """Replace the value of an existing key; True if found.
        O(1) average, O(n) worst."""
        current = self.slots[self.hash(key)]
        while current is not None:
            if current.key == key:
                current.value = value
                return True
            current = current.next
        return False

    def delete(self, key):
        """Remove key; True if it existed.

        Walk the chain keeping a 'previous' pointer, then unlink the node.
        O(1) average, O(n) worst.
        """
        index = self.hash(key)
        previous = None
        current = self.slots[index]
        while current is not None:
            if current.key == key:
                if previous is None:
                    self.slots[index] = current.next
                else:
                    previous.next = current.next
                self.count -= 1
                return True
            previous = current
            current = current.next
        return False

    def _rehash(self):
        """Grow to the next prime >= 2*size and re-insert every node.

        Needed because the slot index depends on size.  O(n).
        """
        old_slots = self.slots
        self.rehash_count += 1
        self.size = next_prime(self.size * 2)
        self.slots = [None] * self.size
        self.count = 0
        self.collisions = 0
        for head in old_slots:
            current = head
            while current is not None:
                self.insert(current.key, current.value)
                current = current.next

    def get_slots(self):
        """List (one per slot) of the keys in each chain, for display. O(n)."""
        result = []
        for head in self.slots:
            chain = []
            current = head
            while current is not None:
                chain.append(current.key)
                current = current.next
            result.append(chain)
        return result

    # ---- optional trace / statistics helpers (do not change the logic) ----
    def search_trace(self, key):
        """Like search() but also explains what happened.

        Returns (value_or_None, slot, steps) where steps is a list of
        (chain_key, matched) in the order the chain was walked.  The number
        of comparisons is len(steps).  O(1) average, O(n) worst.
        """
        slot = self.hash(key)
        steps = []
        current = self.slots[slot]
        while current is not None:
            matched = current.key == key
            steps.append((current.key, matched))
            if matched:
                return current.value, slot, steps
            current = current.next
        return None, slot, steps

    def chain_position(self, key):
        """(slot, 1-based position in chain) or (slot, 0) if absent."""
        _, slot, steps = self.search_trace(key)
        if steps and steps[-1][1]:
            return slot, len(steps)
        return slot, 0

    def longest_chain(self):
        """Length of the longest chain. O(n)."""
        longest = 0
        for chain in self.get_slots():
            if len(chain) > longest:
                longest = len(chain)
        return longest

    def empty_slots(self):
        """Number of slots with no records. O(size)."""
        empty = 0
        for head in self.slots:
            if head is None:
                empty += 1
        return empty
