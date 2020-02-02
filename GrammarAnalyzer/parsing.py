from .firsts_follows_tools import compute_firsts, compute_follows
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
        :return:
            Grammar
        """
        return self._G

    @property
    def Firsts(self):
        return self._firsts

    @property
    def Follows(self):
        return self._follows

    @property
    def Table(self):
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
        self._augmented_grammar = G.AugmentedGrammar()
        self._automaton = self._build_automaton()
        self.verbose = verbose
        super(ShiftReduceParser, self).__init__(G)
        self.action, self.goto = self.Table

    def _build_automaton(self):
        raise NotImplementedError()

    def _lookaheads(self, item):
        raise NotImplementedError()

    @staticmethod
    def _register(table, key, value):
        assert key not in table or table[key] == value, 'Shift-Reduce or Reduce-Reduce conflict!!!'
        table[key] = value

    def _build_parsing_table(self):
        """
        Build de parsing table\n
        :return:\n
        \tReturn a tuple (action, goto) parsing tables
        """
        action = {}
        goto = {}
        G = self._augmented_grammar
        automaton = self._automaton

        for i, node in enumerate(automaton):
            if self.verbose:
                print(i, '\t', '\n\t '.join(str(x) for x in node.state), '\n')
            node.idx = i

        for node in automaton:
            idx = node.idx
            for item in node.state:
                if item.IsReduceItem:
                    if item.production.Left == G.startSymbol:
                        self._register(action, (idx, G.EOF), (self.OK, None))
                    else:
                        for lookahead in self._lookaheads(item):
                            self._register(action, (idx, lookahead), (self.REDUCE, item.production))
                else:
                    symbol = item.NextSymbol
                    idj = node.get(symbol.Name).idx
                    if symbol.IsTerminal:
                        self._register(action, (idx, symbol), (self.SHIFT, idj))
                    else:
                        self._register(goto, (idx, symbol), idj)
        return action, goto

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
                stack += [lookahead.token_type, lookahead.lex, tag]
                cursor += 1
            elif action == self.REDUCE:
                output.append(tag)

                head, body = tag
                
                try:
                    attribute = tag.attributes[0]  # La gramatica es atributada
                except AttributeError:
                    attribute = None  # La gramatica es no atributada

                syn = [None] * (len(body) + 1)
                for i, symbol in enumerate(reversed(body), 1):
                    stack.pop()
                    syn[-i] = stack.pop()
                    assert symbol == stack.pop(), 'Bad Reduce'
                syn[0] = attribute(syn) if attribute is not None else None

                state = stack[-1]
                goto = self.goto[state, head]
                stack += [head, syn[0], goto]

            elif action == self.OK:
                return (output, stack[2]) if get_ast else output
            else:
                raise Exception('Parsing error...')


class SLR1Parser(ShiftReduceParser):
    def _build_automaton(self):
        G = self._augmented_grammar
        return build_LR0_automaton(G)

    def _lookaheads(self, item):
        return self.Follows[item.production.Left]


class LR1Parser(ShiftReduceParser):
    def _build_automaton(self):
        G = self._augmented_grammar
        return build_LR1_automaton(G, firsts=self.Firsts)

    def _lookaheads(self, item):
        return item.lookaheads


class LALR1Parser(LR1Parser):
    def _build_automaton(self):
        G = self._augmented_grammar
        return build_LALR1_automaton(G, firsts=self.Firsts)
