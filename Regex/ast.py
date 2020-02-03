from cmp.ast import UnaryNode, BinaryNode, AtomicNode
from .automata import DFA, automata_closure, automata_concatenation, automata_union

EPSILON = 'ε'


class EpsilonNode(AtomicNode):
    def evaluate(self):
        return DFA(states=1, finals=[0], transitions={})


class SymbolNode(AtomicNode):
    def evaluate(self):
        s = self.lex
        return DFA(states=2, finals=[1], transitions={(0, s): 1})


class ClosureNode(UnaryNode):
    @staticmethod
    def operate(value):
        return automata_closure(value)


class UnionNode(BinaryNode):
    @staticmethod
    def operate(lvalue, rvalue):
        return automata_union(lvalue, rvalue)


class ConcatNode(BinaryNode):
    @staticmethod
    def operate(lvalue, rvalue):
        return automata_concatenation(lvalue, rvalue)


class OptionNode(AtomicNode):
    def __init__(self):
        self.lex = '[]'
        self.inner_nodes = []

    def evaluate(self):
        try:
            node = self.inner_nodes[0]
            for n in self.inner_nodes[1:]:
                node = UnionNode(node, n)
        except IndexError:
            node = EpsilonNode(EPSILON)

        return node.evaluate()


    def __add__(self, other):
        node = OptionNode()

        if isinstance(other, (SymbolNode, RangeNode)):
            node.inner_nodes = self.inner_nodes + [other]
        
        elif isinstance(other, OptionNode):
            node = self.inner_nodes + other.inner_nodes

        node.lex = str(node)
        return node

    def __str__(self):
        s = '['
        for node in self.inner_nodes:
            s += str(node)
        s += ']'
        return s


class RangeNode(BinaryNode):
    def evaluate(self):
        lvalue = self.left.lex
        rvalue = self.right.lex
        return self.operate(lvalue, rvalue)

    @staticmethod
    def operate(lvalue, rvalue):
        node = SymbolNode(lvalue)
        for n in range(ord(lvalue) + 1, ord(rvalue) + 1):
            node = UnionNode(node, SymbolNode(chr(n)))
        return node.evaluate()

    def __str__(self):
        return f'{str(self.left)}-{str(self.right)}'


class QuestionNode(UnaryNode):
    @staticmethod
    def operate(value):
        return automata_union(value, EpsilonNode(EPSILON).evaluate())
    
    def __str__(self):
        return str(self.node) + '?'


class PlusNode(UnaryNode):
    @staticmethod
    def operate(value):
        return automata_concatenation(value, automata_closure(value))
    
    def __str__(self):
        return str(self.node) + '+'
