from .utils import regex_tokenizer
from .ast import EpsilonNode, SymbolNode, UnionNode, ConcatNode, ClosureNode, QuestionNode, RangeNode, PlusNode, OptionNode
from .automata import DFA
from cmp.pycompiler import Grammar


class Regex:
    def __init__(self, regex, skip_whitespaces=False):
        self.regex = regex
        self.automaton = self.build_automaton(regex)

    def __call__(self, text):
        return self.automaton.recognize(text)

    @staticmethod
    def build_automaton(regex, skip_whitespaces=False):
        G = Regex.__grammar()
        tokens = regex_tokenizer(regex, G, skip_whitespaces=False)
        left_parse = parser(tokens)
        ast = evaluate_parse(left_parse, tokens)
        nfa = ast.evaluate()
        dfa = DFA.from_nfa(nfa)
        dfa = DFA.minimize(dfa)
        return dfa
    

    @staticmethod
    def __grammar():
        G = Grammar()

        E = G.NonTerminal('E', True)
        T, F, A, X, Y, Z, L, R = G.NonTerminals('T F A X Y Z L R')
        pipe, star, opar, cpar, symbol, epsilon, osquare, csquare, question, plus, minus = G.Terminals('| * ( ) symbol ε [ ] ? + -')

        E %= E + pipe + T
        
        T %= T + F 
        
        F %= A + star
        F %= A + question
        F %= A + plus

        A %= symbol
        A %= opar + E + cpar
        A %= osquare + L + csquare

        L %= symbol + minus + symbol + L
        L %= symbol + L



        # =================== PRODUCTIONS =================== #
        # > union :
        E %= T + X, lambda h,s: s[2], None, lambda h,s: s[1]
        X %= pipe + E, lambda h,s: s[2], None, lambda h,s: UnionNode(h[0], s[2])
        X %= G.Epsilon, lambda h,s: h[0]

        # > concatenacion :
        T %= F + Y, lambda h,s: s[2], None, lambda h,s: s[1]
        Y %= T, lambda h,s: ConcatNode(h[0], s[1])
        Y %= G.Epsilon, lambda h,s: h[0]

        # > clausura :
        F %= A + Z, lambda h,s: s[2], None, lambda h,s: s[1] 
        Z %= star, lambda h,s: ClosureNode(h[0])
        Z %= question, lambda h,s: QuestionNode(h[0])
        Z %= plus, lambda h,s: PlusNode(h[0])
        Z %= G.Epsilon, lambda h,s: h[0]

        # > atomicos :
        A %= symbol, lambda h,s: SymbolNode(s[1])
        A %= epsilon, lambda h,s: EpsilonNode(s[1])
        A %= osquare + L + csquare, lambda h,s: s[2], None, lambda h,s: OptionNode(), None
        A %= opar + E + cpar, lambda h,s: s[2]

        L %= symbol + R, lambda h,s: s[2], None, lambda h,s: (h[0], SymbolNode(s[1]))
        L %= G.Epsilon, lambda h,s: h[0]
        R %= minus + symbol + L, lambda h,s: s[3], None, None, lambda h,s: h[0][0] + RangeNode(h[0][1], SymbolNode(s[2]))
        R %= L, lambda h,s: s[1], lambda h,s: h[0][0] + h[0][1]

        return G
