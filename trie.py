class TrieNode:
    def __init__(self, symbol, parent=None, final=False):
        self.symbol = symbol
        self.parent = parent
        self.childs = {}
        self.count = 1
        self.final = final

    def add(self, symbol):
        try:
            self.childs[symbol]
        except KeyError:
            self.childs[symbol] = TrieNode(symbol, parent=self)

    def __getitem__(self, item):
        return self.childs[item]

    def __setitem__(self, key, value):
        self.childs[key] = value

    def __contains__(self, item):
        return item in self.childs

    def __iter__(self):
        yield from self.childs

    def __eq__(self, other):
        return self.symbol == other.symbol


class Trie:
    def __init__(self):
        self.root: TrieNode = TrieNode('^')
        self.root.count = 0

    def insert(self, sentence):
        index, node = self.__maximum_common_prefix(sentence)
        for symbol in sentence[index:]:
            node.add(symbol)
            node = node[symbol]
        node.final = True
        self.root.count += 1

    def extend(self, *sentences):
        for s in sentences:
            self.insert(s)

    def __maximum_common_prefix(self, sentence):
        current: TrieNode = self.root
        for i, symbol in enumerate(sentence):
            try:
                current = current[symbol]
                current.count += 1
            except KeyError:
                return i, current
        return len(sentence), current

    def __from_prefix(self, prefix):
        node: TrieNode = self.root
        for symbol in prefix:
            try:
                node = node[symbol]
            except KeyError:
                return []

        yield from Trie.__search_from_node(node, prefix)

    @staticmethod
    def __search_from_node(node, sentence):
        if node.final:
            yield sentence

        for child in node:
            yield from Trie.__search_from_node(node[child], sentence + child)

    def __len__(self):
        return self.root.count

    def __iter__(self):
        yield from self.__search_from_node(self.root, "")

    def __call__(self, prefix):
        yield from self.__from_prefix(prefix)

    def __contains__(self, item):
        i, node = self.__maximum_common_prefix(item)
        return i == len(item) and node.final
