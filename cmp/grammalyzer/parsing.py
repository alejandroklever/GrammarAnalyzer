from enum import auto, Enum

from .automatas import build_lr0_automaton, build_lr1_automaton, build_larl1_automaton
from .utils import compute_firsts, compute_follows


class LRConflictType(Enum):
    """
    Enum for mark the type of a lr-family parser
    """
    ReduceReduce = auto()
    ShiftReduce = auto()


class LRConflict:
    def __init__(self, state, symbol, ctype):
        self.state = state
        self.symbol = symbol
        self.cType = ctype

    def __iter__(self):
        yield self.state
        yield self.symbol


class LLConflictType(Enum):
    """
    Enum for mark the type of a ll parser
    """
    FirstFirst = auto()
    FollowFollow = auto()


class LLConflict:
    def __init__(self, nontermial, terminal, ctype):
        self.nonterminal = nontermial
        self.terminal = terminal
        self.cType = ctype

    def __iter__(self):
        yield self.nonterminal
        yield self.terminal


class LL1Parser:
    def __init__(self, G):
        self.G = G
        self.firsts = compute_firsts(G)
        self.follows = compute_follows(G, self.firsts)
        self.conflict = None
        self.table = self._build_parsing_table()

    def _build_parsing_table(self):
        G = self.G
        firsts = self.firsts
        follows = self.follows
        parsing_table = {}

        # P: X -> alpha
        for production in G.Productions:
            head, body = production

            contains_epsilon = firsts[body].contains_epsilon

            # working with symbols on First(alpha) ...
            if not contains_epsilon:
                for symbol in firsts[body]:
                    try:
                        parsing_table[head, symbol].append(production)
                        self.conflict = LLConflict(head, symbol, LLConflictType.FirstFirst)
                    except KeyError:
                        parsing_table[head, symbol] = [production]
            # working with epsilon...
            else:
                for symbol in follows[head]:
                    try:
                        parsing_table[head, symbol].append(production)
                        self.conflict = LLConflict(head, symbol, LLConflictType.FollowFollow)
                    except KeyError:
                        parsing_table[head, symbol] = [production]

        # parsing table is ready!!!
        return parsing_table

    def __call__(self, tokens):
        G = self.G
        table = self.table

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


class ShiftReduceParser:
    SHIFT = 'SHIFT'
    REDUCE = 'REDUCE'
    OK = 'OK'

    def __init__(self, G, verbose=False):
        self.G = G
        self.augmented_G = G.AugmentedGrammar(True)
        self.firsts = compute_firsts(self.augmented_G)
        self.follows = compute_follows(self.augmented_G, self.firsts)
        self.automaton = self._build_automaton()
        self.state_dict = {}
        self.conflict = None

        self.verbose = verbose
        self.action = {}
        self.goto = {}
        self._build_parsing_table()

        if self.conflict is None:
            self._clean_tables()

    def _build_parsing_table(self):
        G = self.augmented_G
        automaton = self.automaton

        for i, node in enumerate(automaton):
            if self.verbose:
                print(i, '\t', '\n\t '.join(str(x) for x in node.state), '\n')
            node.idx = i
            self.state_dict[i] = node

        for node in automaton:
            idx = node.idx
            for item in node.state:
                if item.IsReduceItem:
                    if item.production.Left == G.startSymbol:
                        self._register(self.action, (idx, G.EOF), (self.OK, None))
                    else:
                        for lookahead in self._lookaheads(item):
                            self._register(self.action, (idx, lookahead), (self.REDUCE, item.production))
                else:
                    symbol = item.NextSymbol
                    idj = node.get(symbol.Name).idx
                    if symbol.IsTerminal:
                        self._register(self.action, (idx, symbol), (self.SHIFT, idj))
                    else:
                        self._register(self.goto, (idx, symbol), idj)

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
                    assert symbol == stack.pop(), 'Bad Reduce...'
                syn[0] = attribute(syn) if attribute is not None else None

                state = stack[-1]
                goto = self.goto[state, head]
                stack += [head, syn[0], goto]

            elif action == self.OK:
                return (output, stack[2]) if get_ast else output
            else:
                raise Exception('Parsing error...')

    def _register(self, table, key, value):
        # assert key not in table or table[key] == value, 'Shift-Reduce or Reduce-Reduce conflict!!!'
        try:
            n = len(table[key])
            table[key].add(value)
            if self.conflict is None and n != len(table[key]):
                if all(action == self.REDUCE for action, _ in list(table[key])[:2]):
                    cType = LRConflictType.ReduceReduce
                else:
                    cType = LRConflictType.ShiftReduce

                self.conflict = LRConflict(key[0], key[1], cType)
                self.conflict.value1 = list(table[key])[0]
                self.conflict.value2 = list(table[key])[1]

        except KeyError:
            table[key] = {value}

    def _clean_tables(self):
        for key in self.action:
            self.action[key] = self.action[key].pop()
        for key in self.goto:
            self.goto[key] = self.goto[key].pop()

    def _build_automaton(self):
        raise NotImplementedError()

    def _lookaheads(self, item):
        raise NotImplementedError()


class SLR1Parser(ShiftReduceParser):
    def _build_automaton(self):
        return build_lr0_automaton(self.augmented_G)

    def _lookaheads(self, item):
        return self.follows[item.production.Left]


class LR1Parser(ShiftReduceParser):
    def _build_automaton(self):
        return build_lr1_automaton(self.augmented_G, firsts=self.firsts)

    def _lookaheads(self, item):
        return item.lookaheads


class LALR1Parser(LR1Parser):
    def _build_automaton(self):
        return build_larl1_automaton(self.augmented_G, firsts=self.firsts)
