import pydot


def node_to_str(node, depth):
    s = '    ' * depth + ('\\__' if depth != 0 else '') + f'({str(node.symbol)})' + '\n'
    for child in node.childs:
        s += node_to_str(child, depth + 1)
    return s


class DerivationTreeNode:
    def __init__(self, symbol, father=None):
        self.symbol = symbol
        self.father = father
        self.childs = []

    def add_child(self, symbol):
        self.childs.append(DerivationTreeNode(symbol, father=self))
        return self.childs[-1]

    def go_root(self):
        node = self
        while node.father != None:
            node = node.father
        return node

    def __str__(self):
        return str(self.symbol)

class DerivationTree:
    def __init__(self, productions):
        self.root = self._build_tree(productions)

    def _build_tree(self, productions):
        iter_productions = iter(productions)
        root = self._expand_tree(iter_productions)
        return root

    def _expand_tree(self, productions, node=None):
        try:
            head, body = next(productions)
        except StopIteration:
            return node.go_root()

        if node is None:
            node = DerivationTreeNode(head)

        assert node.symbol == head

        for symbol in body:
            if symbol.IsTerminal:
                node.add_child(symbol)
            elif symbol.IsNonTerminal:
                next_node = node.add_child(symbol)
                self._expand_tree(productions, next_node)
        return node

    def graph(self):
        G = pydot.Dot(graph_type='graph', rankdir='TD', margin=0.1)
        stack = [self.root]
        
        while stack:
            current = stack.pop()
            ids = id(current)
            G.add_node(pydot.Node(name=ids, label=str(current), shape='circle'))
            for child in current.childs:
                stack.append(child)
                G.add_node(pydot.Node(name=id(child), label=str(child), shape='circle'))
                G.add_edge(pydot.Edge(ids, id(child)))
        
        return G
    
    def _repr_svg_(self):
        try:
            return self.graph().create_svg().decode('utf8')
        except:
            pass

    def __str__(self):
        return str(self.root)
