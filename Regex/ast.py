from cmp.ast import UnaryNode, BinaryNode, AtomicNode
from .automata import DFA, automata_closure, automata_concatenation, automata_union


EPSILON = 'ε'

class EpsilonNode(AtomicNode):
    def evaluate(self):
        return DFA(states=1, finals=[0], transitions={})

    def __str__(self):
        return EPSILON


class SymbolNode(AtomicNode):
    def evaluate(self):
        s = self.lex
        return DFA(states=2, finals=[1], transitions={(0, s): 1})

    def __str__(self):
        return self.lex
    
    def __repr__(self):
        return self.__str__()


class ClosureNode(UnaryNode):
    @staticmethod
    def operate(value):
        return automata_closure(value)

    def __str__(self):
        return str(self.node) + '*'

    def __repr__(self):
        return self.__str__()


class UnionNode(BinaryNode):
    @staticmethod
    def operate(lvalue, rvalue):
        return automata_union(lvalue, rvalue)

    def __str__(self):
        return str(self.left) + "|" + str(self.right)

    def __repr__(self):
        return self.__str__()


class ConcatNode(BinaryNode):
    @staticmethod
    def operate(lvalue, rvalue):
        return automata_concatenation(lvalue, rvalue)

    def __str__(self):
        return str(self.left) + str(self.right)

    def __repr__(self):
        return self.__str__()


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

    def __repr__(self):
        return self.__str__()


class QuestionNode(UnaryNode):
    @staticmethod
    def operate(value):
        return automata_union(value, EpsilonNode(EPSILON).evaluate())
    
    def __str__(self):
        return str(self.node) + '?'

    def __repr__(self):
        return self.__str__()

class PlusNode(UnaryNode):
    @staticmethod
    def operate(value):
        return automata_concatenation(value, automata_closure(value))
    
    def __str__(self):
        return str(self.node) + '+'

    def __repr__(self):
        return self.__str__()