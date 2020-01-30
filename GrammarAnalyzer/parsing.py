from cmp.automata import State, multiline_formatter
from cmp.pycompiler import Grammar, Item
from cmp.utils import ContainerSet

from .tools import compute_firsts, compute_follows, compute_local_first
from .lr_automata import build_LR0_automaton, build_LR1_automaton, build_LALR1_automaton


class Parser:
    def __init__(self, G):
        self._G = G
        self._firsts = compute_firsts(G)
        self._follows = compute_follows(G, self._firsts)
        self._table = self._build_parsing_table()

    @property
    def G(self):
        """
        :rtype: Grammar
        """
        return self._G

    @property
    def firsts(self):
        return self.firsts

    @property
    def follows(self):
        return self._follows

    @property
    def table(self):
        return self._table

    def _build_parsing_table(self):
        raise NotImplementedError()


class LL1Parser(Parser):
    def _build_parsing_table(self):
        G = self._G
        firsts = self._firsts
        follows = self._follows
        parsing_table = {}

        # P: X -> alpha
        for production in G.Productions:
            X = production.Left
            alpha = production.Right

            contains_epsilon = firsts[alpha].contains_epsilon

            # working with symbols on First(alpha) ...
            if not contains_epsilon:
                for symbol in firsts[alpha]:
                    parsing_table[X, symbol] = [production]
            # working with epsilon...
            else:
                for symbol in follows[X]:
                    parsing_table[X, symbol] = [production]

        # parsing table is ready!!!
        return parsing_table

    def __call__(self, tokens):
        G = self._G
        table = self._table

        stack = [G.startSymbol]
        cursor = 0
        output = []

        # parsing w...
        while len(stack) > 0 and cursor < len(tokens):
            top = stack.pop()
            currentToken = tokens[cursor].token_type
            # print((top, currentToken))
            if top.IsTerminal:
                cursor += 1
                if currentToken != top:
                    return None
            elif top.IsNonTerminal:
                try:
                    production = table[top, currentToken][0]
                except KeyError:
                    return None

                output.append(production)
                reversed_production = reversed(production.Right)

                for s in reversed_production:
                    stack.append(s)

        # left parse is ready!!!
        return output


class ShiftReduceParser(Parser):
    SHIFT = 'SHIFT'
    REDUCE = 'REDUCE'
    OK = 'OK'

    def __init__(self, G, verbose=False):
        self._G = G
        self._firsts = compute_firsts(G)
        self._follows = compute_follows(G, self._firsts)
        self.verbose = verbose
        self.action = {}
        self.goto = {}
        self._build_parsing_table()

    @property
    def automaton_builder(self):
        raise NotImplementedError()

    def _build_parsing_table(self):
        raise NotImplementedError()

    def __call__(self, tokens, get_ast=False):
        stack = [0]
        cursor = 0
        output = []

        while True:
            state = stack[-1]
            lookahead = tokens[cursor]
            if self.verbose:
                print(stack, '<---||--->', tokens[cursor:])

            assert (state, lookahead.token_type) in self.action, 'Parsing Error...'

            action, tag = self.action[state, lookahead.token_type]

            if action == self.SHIFT:
                stack += [lookahead, lookahead.lex, tag]
                cursor += 1
            elif action == self.REDUCE:
                output.append(tag)

                head, body = tag
                attributes = tag.attributes[0]
                syn = [None] * (len(body) + 1)

                for i, symbol in enumerate(reversed(body), 1):
                    stack.pop()
                    syn[-i] = stack.pop()
                    assert symbol == stack.pop(), 'Bad Reduce'
                syn[0] = attributes(syn) if attributes is not None else None

                state = stack[-1]
                goto = self.goto[state, head]
                stack += [head, syn[0], goto]

            elif action == self.OK:
                return (output, stack[2]) if get_ast else output
            else:
                raise Exception('Parsing error...')


class SLR1Parser(ShiftReduceParser):
    @property
    def automaton_builder(self):
        return build_LR0_automaton

    def _build_parsing_table(self):
        G = self.G.AugmentedGrammar(True)
        firsts = compute_firsts(G)
        follows = compute_follows(G, firsts)

        automaton = self.automaton_builder(G)
        for i, node in enumerate(automaton):
            if self.verbose:
                print(i, '\t', '\n\t '.join(str(x) for x in node.state), '\n')
            node.idx = i

        for node in automaton:
            idx = node.idx
            for item in node.state:
                if item.IsReduceItem:
                    head, _ = item.production
                    if head == G.startSymbol:
                        self._register(self.action, (idx, G.EOF), (self.OK, None))
                    else:
                        for c in follows[head]:
                            self._register(self.action, (idx, c), (self.REDUCE, item.production))
                else:
                    symbol = item.NextSymbol
                    idj = node.get(symbol.Name).idx
                    if symbol.IsTerminal:
                        self._register(self.action, (idx, symbol), (self.SHIFT, idj))
                    else:
                        self._register(self.goto, (idx, symbol), idj)

    @staticmethod
    def _register(table, key, value):
        assert key not in table or table[key] == value, 'Shift-Reduce or Reduce-Reduce conflict!!!'
        table[key] = value


class LR1Parser(ShiftReduceParser):
    @property
    def automaton_builder(self):
        return build_LR1_automaton

    def _build_parsing_table(self):
        G = self.G.AugmentedGrammar(True)

        automaton = self.automaton_builder(G, firsts=self.firsts)
        for i, node in enumerate(automaton):
            if self.verbose:
                print(i, '\t', '\n\t '.join(str(x) for x in node.state), '\n')
            node.idx = i

        for node in automaton:
            idx = node.idx
            for item in node.state:
                if item.IsReduceItem:
                    if item.production.Left == G.startSymbol:
                        self._register(self.action, (idx, G.EOF), (self.OK, None))
                    else:
                        for lookahead in item.lookaheads:
                            self._register(self.action, (idx, lookahead), (self.REDUCE, item.production))
                else:
                    symbol = item.NextSymbol
                    idj = node.get(symbol.Name).idx
                    if symbol.IsTerminal:
                        self._register(self.action, (idx, symbol), (self.SHIFT, idj))
                    else:
                        self._register(self.goto, (idx, symbol), idj)

    @staticmethod
    def _register(table, key, value):
        assert key not in table or table[key] == value, 'Shift-Reduce or Reduce-Reduce conflict!!!'
        table[key] = value


class LALR1Parser(LR1Parser):
    @property
    def automaton_builder(self):
        return build_LALR1_automaton
