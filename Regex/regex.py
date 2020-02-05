from cmp.pycompiler import Grammar
from cmp.utils import Token
from GrammarAnalyzer import LR1Parser

from .ast import (ClosureNode, ConcatNode, EpsilonNode, PlusNode, QuestionNode,
                  RangeNode, SymbolNode, UnionNode)
from .automata import DFA


class Regex:
    def __init__(self, regex, skip_whitespaces=False):
        self.regex = regex
        self.automaton = self.build_automaton(regex)

    def __call__(self, text):
        return self.automaton.recognize(text)


    @staticmethod
    def build_automaton(regex, skip_whitespaces=False):
        G = Regex.Grammar()
        tokens = regex_tokenizer(regex, G, skip_whitespaces=False)
        _, ast = LR1Parser(G)(tokens, get_ast=True)
        nfa = ast.evaluate()
        dfa = DFA.from_nfa(nfa)
        return DFA.minimize(dfa)
    

    @staticmethod
    def Grammar():
        G = Grammar()

        E = G.NonTerminal('E', True)
        T, F, A, L = G.NonTerminals('T F A L')
        pipe, star, opar, cpar, symbol, epsilon, osquare, csquare, minus, plus, question = G.Terminals('| * ( ) symbol ε [ ] - + ?')

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


def regex_tokenizer(text, G, skip_whitespaces=True):
    tokens = []
    fixed_tokens = { lex: Token(lex, G[lex]) for lex in '| * ( ) ε [ ] ? + -'.split()}
    open_pos = 0
    inside_squares = False
    for i, char in enumerate(text):
        if skip_whitespaces and char.isspace():
            continue

        if not inside_squares:
            if char in (']',  '-') or char not in fixed_tokens:
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
                if (i + 1 < len(text) and text[i + 1] == ']') or text[i - 1] == '[':
                    tokens.append(Token(char, G['symbol']))
                elif i - 2 > open_pos and tokens[-2].token_type == G['-']:
                    tokens.append(Token(char, G['symbol']))
                elif (i - 1 > open_pos and text[i-1] == '-') or (i + 1 < len(text) and text[i + 1] == '-'):
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
    return (i + 1 < len(text) and text[i + 1] == ']') \
            or (text[i - 1] == '[') \
            or (i - 2 > open_pos and tokens[-2].token_type == G['-']) \
            or (i - 1 > open_pos and text[i-1] == '-') \
            or (i + 1 < len(text) and text[i + 1] == '-')
