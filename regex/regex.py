from cmp.pycompiler import Grammar, AttributeProduction, Sentence
from cmp.utils import Token
from grammalyzer import ShiftReduceParser

from .ast import (ClosureNode, ConcatNode, EpsilonNode, PlusNode, QuestionNode,
                  RangeNode, SymbolNode, UnionNode)
from .automata import DFA


class Regex:
    def __init__(self, regex, skip_whitespaces=False):
        self.regex = regex
        self.automaton = self.build_automaton(regex, skip_whitespaces)

    def __call__(self, text):
        return self.automaton.recognize(text)

    @staticmethod
    def build_automaton(regex, skip_whitespaces=False):
        parser = RegexParser(verbose=False)
        tokens = regex_tokenizer(regex, parser.G, skip_whitespaces)
        _, ast = parser(tokens, get_ast=True)
        nfa = ast.evaluate()
        dfa = DFA.from_nfa(nfa)
        dfa = DFA.minimize(dfa)
        return dfa

    @staticmethod
    def Grammar():
        G = Grammar()

        E = G.NonTerminal('E', True)
        T, F, A, L = G.NonTerminals('T F A L')
        pipe, star, opar, cpar, symbol, epsilon, osquare, csquare, minus, plus, question = G.Terminals(
            '| * ( ) symbol ε [ ] - + ?')

        E %= E + pipe + T, lambda s: UnionNode(s[1], s[3])
        E %= T, lambda s: s[1]

        T %= T + F, lambda s: ConcatNode(s[1], s[2])
        T %= F, lambda s: s[1]

        F %= A + star, lambda s: ClosureNode(s[1])
        F %= A + plus, lambda s: PlusNode(s[1])
        F %= A + question, lambda s: QuestionNode(s[1])
        F %= A, lambda s: s[1]

        A %= symbol, lambda s: SymbolNode(s[1])
        A %= epsilon, lambda s: EpsilonNode(s[1])
        A %= opar + E + cpar, lambda s: s[2]
        A %= osquare + L + csquare, lambda s: s[2]

        L %= symbol, lambda s: SymbolNode(s[1])
        L %= symbol + minus + symbol, lambda s: RangeNode(SymbolNode(s[1]), SymbolNode(s[3]))
        L %= symbol + L, lambda s: UnionNode(SymbolNode(s[1]), s[2])
        L %= symbol + minus + symbol + L, lambda s: UnionNode(RangeNode(SymbolNode(s[1]), SymbolNode(s[3])), s[4])

        return G


# noinspection PyAbstractClass
class RegexParser(ShiftReduceParser):
    def __init__(self, verbose=False):
        G = Grammar()
        G.NonTerminal('E', True)
        G.NonTerminals('T F A L')
        G.Terminals('| * ( ) symbol ε [ ] - + ?')

        self.G = G
        self.verbose = verbose
        self.action = self.__action_table()
        self.goto = self.__goto_table()

    def __action_table(self):
        G = self.G
        return {
            (0, G["ε"]): ("SHIFT", 27),
            (0, G["("]): ("SHIFT", 1),
            (0, G["["]): ("SHIFT", 28),
            (0, G["symbol"]): ("SHIFT", 26),
            (1, G["["]): ("SHIFT", 5),
            (1, G["symbol"]): ("SHIFT", 3),
            (1, G["ε"]): ("SHIFT", 4),
            (1, G["("]): ("SHIFT", 2),
            (2, G["["]): ("SHIFT", 5),
            (2, G["symbol"]): ("SHIFT", 3),
            (2, G["ε"]): ("SHIFT", 4),
            (2, G["("]): ("SHIFT", 2),
            (3, G["|"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (3, G["+"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (3, G["?"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (3, G["*"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (3, G["("]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (3, G[")"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (3, G["symbol"]): (
                "REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (3, G["ε"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (3, G["["]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (4, G["|"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (4, G["+"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (4, G["?"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (4, G["*"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (4, G["("]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (4, G[")"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (4, G["symbol"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (4, G["ε"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (4, G["["]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (5, G["symbol"]): ("SHIFT", 6),
            (6, G["]"]): ("REDUCE", AttributeProduction(G["L"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (6, G["-"]): ("SHIFT", 7),
            (6, G["symbol"]): ("SHIFT", 6),
            (7, G["symbol"]): ("SHIFT", 8),
            (8, G["]"]): ("REDUCE", AttributeProduction(G["L"], Sentence(G["symbol"], G["-"], G["symbol"]),
                                                        [lambda s: RangeNode(SymbolNode(s[1]), SymbolNode(s[3]))])),
            (8, G["symbol"]): ("SHIFT", 6),
            (9, G["]"]): ("REDUCE", AttributeProduction(G["L"], Sentence(G["symbol"], G["-"], G["symbol"], G["L"]), [
                lambda s: UnionNode(RangeNode(SymbolNode(s[1]), SymbolNode(s[3])), s[4])])),
            (10, G["]"]): ("REDUCE", AttributeProduction(G["L"], Sentence(G["symbol"], G["L"]),
                                                         [lambda s: UnionNode(SymbolNode(s[1]), s[2])])),
            (11, G["]"]): ("SHIFT", 12),
            (12, G["|"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (12, G["+"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (12, G["?"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (12, G["*"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (12, G["("]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (12, G[")"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (12, G["symbol"]): (
                "REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (12, G["ε"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (12, G["["]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (13, G["|"]): ("SHIFT", 14),
            (13, G[")"]): ("SHIFT", 22),
            (14, G["["]): ("SHIFT", 5),
            (14, G["symbol"]): ("SHIFT", 3),
            (14, G["ε"]): ("SHIFT", 4),
            (14, G["("]): ("SHIFT", 2),
            (15, G["["]): ("SHIFT", 5),
            (15, G["symbol"]): ("SHIFT", 3),
            (15, G["ε"]): ("SHIFT", 4),
            (15, G["|"]): (
                "REDUCE",
                AttributeProduction(G["E"], Sentence(G["E"], G["|"], G["T"]), [lambda s: UnionNode(s[1], s[3])])),
            (15, G[")"]): (
                "REDUCE",
                AttributeProduction(G["E"], Sentence(G["E"], G["|"], G["T"]), [lambda s: UnionNode(s[1], s[3])])),
            (15, G["("]): ("SHIFT", 2),
            (16, G["|"]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (16, G["("]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (16, G[")"]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (16, G["symbol"]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (16, G["ε"]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (16, G["["]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (17, G["*"]): ("SHIFT", 18),
            (17, G["|"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (17, G["("]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (17, G[")"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (17, G["symbol"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (17, G["ε"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (17, G["["]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (17, G["+"]): ("SHIFT", 19),
            (17, G["?"]): ("SHIFT", 20),
            (18, G["|"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (18, G["("]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (18, G[")"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (18, G["symbol"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (18, G["ε"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (18, G["["]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (19, G["|"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (19, G["("]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (19, G[")"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (19, G["symbol"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (19, G["ε"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (19, G["["]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (20, G["|"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (20, G["("]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (20, G[")"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (20, G["symbol"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (20, G["ε"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (20, G["["]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (21, G["|"]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (21, G["("]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (21, G[")"]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (21, G["symbol"]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (21, G["ε"]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (21, G["["]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (22, G["|"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (22, G["+"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (22, G["?"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (22, G["*"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (22, G["("]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (22, G[")"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (22, G["symbol"]): (
                "REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (22, G["ε"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (22, G["["]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (23, G["["]): ("SHIFT", 5),
            (23, G["symbol"]): ("SHIFT", 3),
            (23, G["|"]): ("REDUCE", AttributeProduction(G["E"], Sentence(G["T"]), [lambda s: s[1]])),
            (23, G[")"]): ("REDUCE", AttributeProduction(G["E"], Sentence(G["T"]), [lambda s: s[1]])),
            (23, G["ε"]): ("SHIFT", 4),
            (23, G["("]): ("SHIFT", 2),
            (24, G["|"]): ("SHIFT", 14),
            (24, G[")"]): ("SHIFT", 25),
            (25, G["|"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (25, G["+"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (25, G["?"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (25, G["*"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (25, G["("]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (25, G["symbol"]): (
                "REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (25, G["$"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (25, G["ε"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (25, G["["]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["("], G["E"], G[")"]), [lambda s: s[2]])),
            (26, G["|"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (26, G["+"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (26, G["?"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (26, G["*"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (26, G["("]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (26, G["symbol"]): (
                "REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (26, G["$"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (26, G["ε"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (26, G["["]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["symbol"]), [lambda s: SymbolNode(s[1])])),
            (27, G["|"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (27, G["+"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (27, G["?"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (27, G["*"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (27, G["("]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (27, G["symbol"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (27, G["$"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (27, G["ε"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (27, G["["]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["ε"]), [lambda s: EpsilonNode(s[1])])),
            (28, G["symbol"]): ("SHIFT", 6),
            (29, G["]"]): ("SHIFT", 30),
            (30, G["|"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (30, G["+"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (30, G["?"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (30, G["*"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (30, G["("]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (30, G["symbol"]): (
                "REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (30, G["ε"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (30, G["$"]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (30, G["["]): ("REDUCE", AttributeProduction(G["A"], Sentence(G["["], G["L"], G["]"]), [lambda s: s[2]])),
            (31, G["|"]): ("SHIFT", 32),
            (31, G["$"]): ("OK", None),
            (32, G["ε"]): ("SHIFT", 27),
            (32, G["("]): ("SHIFT", 1),
            (32, G["["]): ("SHIFT", 28),
            (32, G["symbol"]): ("SHIFT", 26),
            (33, G["ε"]): ("SHIFT", 27),
            (33, G["("]): ("SHIFT", 1),
            (33, G["["]): ("SHIFT", 28),
            (33, G["|"]): (
                "REDUCE",
                AttributeProduction(G["E"], Sentence(G["E"], G["|"], G["T"]), [lambda s: UnionNode(s[1], s[3])])),
            (33, G["$"]): (
                "REDUCE",
                AttributeProduction(G["E"], Sentence(G["E"], G["|"], G["T"]), [lambda s: UnionNode(s[1], s[3])])),
            (33, G["symbol"]): ("SHIFT", 26),
            (34, G["|"]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (34, G["("]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (34, G["symbol"]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (34, G["ε"]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (34, G["$"]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (34, G["["]): (
                "REDUCE", AttributeProduction(G["T"], Sentence(G["T"], G["F"]), [lambda s: ConcatNode(s[1], s[2])])),
            (35, G["*"]): ("SHIFT", 36),
            (35, G["|"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (35, G["("]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (35, G["symbol"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (35, G["ε"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (35, G["$"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (35, G["["]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"]), [lambda s: s[1]])),
            (35, G["+"]): ("SHIFT", 37),
            (35, G["?"]): ("SHIFT", 38),
            (36, G["|"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (36, G["("]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (36, G["symbol"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (36, G["ε"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (36, G["$"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (36, G["["]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["*"]), [lambda s: ClosureNode(s[1])])),
            (37, G["|"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (37, G["("]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (37, G["symbol"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (37, G["ε"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (37, G["$"]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (37, G["["]): ("REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["+"]), [lambda s: PlusNode(s[1])])),
            (38, G["|"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (38, G["("]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (38, G["symbol"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (38, G["$"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (38, G["ε"]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (38, G["["]): (
                "REDUCE", AttributeProduction(G["F"], Sentence(G["A"], G["?"]), [lambda s: QuestionNode(s[1])])),
            (39, G["|"]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (39, G["("]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (39, G["symbol"]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (39, G["$"]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (39, G["ε"]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (39, G["["]): ("REDUCE", AttributeProduction(G["T"], Sentence(G["F"]), [lambda s: s[1]])),
            (40, G["ε"]): ("SHIFT", 27),
            (40, G["("]): ("SHIFT", 1),
            (40, G["|"]): ("REDUCE", AttributeProduction(G["E"], Sentence(G["T"]), [lambda s: s[1]])),
            (40, G["$"]): ("REDUCE", AttributeProduction(G["E"], Sentence(G["T"]), [lambda s: s[1]])),
            (40, G["["]): ("SHIFT", 28),
            (40, G["symbol"]): ("SHIFT", 26),
        }

    def __goto_table(self):
        G = self.G
        return {
            (0, G["T"]): 40,
            (0, G["E"]): 31,
            (0, G["A"]): 35,
            (0, G["F"]): 39,
            (1, G["T"]): 23,
            (1, G["F"]): 21,
            (1, G["A"]): 17,
            (1, G["E"]): 24,
            (2, G["T"]): 23,
            (2, G["F"]): 21,
            (2, G["A"]): 17,
            (2, G["E"]): 13,
            (5, G["L"]): 11,
            (6, G["L"]): 10,
            (8, G["L"]): 9,
            (14, G["F"]): 21,
            (14, G["T"]): 15,
            (14, G["A"]): 17,
            (15, G["A"]): 17,
            (15, G["F"]): 16,
            (23, G["A"]): 17,
            (23, G["F"]): 16,
            (28, G["L"]): 29,
            (32, G["A"]): 35,
            (32, G["F"]): 39,
            (32, G["T"]): 33,
            (33, G["F"]): 34,
            (33, G["A"]): 35,
            (40, G["F"]): 34,
            (40, G["A"]): 35,
        }


def regex_tokenizer(text, G, skip_whitespaces=True):
    tokens = []
    fixed_tokens = {lex: Token(lex, G[lex]) for lex in '| * ( ) ε [ ] ? + -'.split()}
    open_pos = 0
    inside_squares = False
    set_literal = False
    for i, char in enumerate(text):
        if skip_whitespaces and char.isspace():
            continue

        if not set_literal and char == '\\':
            set_literal = True
            continue

        if set_literal:
            tokens.append(Token(char, G['symbol']))
            set_literal = False
            continue

        if not inside_squares:
            if char in (']', '-') or char not in fixed_tokens:
                tokens.append(Token(char, G['symbol']))
            else:
                tokens.append(fixed_tokens[char])

            open_pos = i
            inside_squares = char == '['

        else:
            if char == ']':
                if i - open_pos == 1:
                    tokens.append(Token(char, G['symbol']))
                else:
                    inside_squares = False
                    tokens.append(fixed_tokens[char])
            elif char == '-':
                if is_minus_a_symbol(G, text, tokens, i, open_pos):
                    tokens.append(Token(char, G['symbol']))
                else:
                    tokens.append(fixed_tokens[char])
            else:
                tokens.append(Token(char, G['symbol']))

    if inside_squares:
        raise Exception(f'Unterminated character set at position {open_pos}')

    tokens.append(Token('$', G.EOF))
    return tokens


def is_minus_a_symbol(G, text, tokens, i, open_pos):
    return (i + 1 < len(text) and text[i + 1] == ']') or (text[i - 1] == '[') or \
           (i - 2 > open_pos and tokens[-2].token_type == G['-']) or \
           (i - 1 > open_pos and text[i - 1] == '-') or (i + 1 < len(text) and text[i + 1] == '-')
