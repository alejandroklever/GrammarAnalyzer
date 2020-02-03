from cmp.automata import State, multiline_formatter
from cmp.pycompiler import Item
from cmp.utils import ContainerSet

from .utils import compute_firsts, compute_local_first


##### SLR AUTOMATA #####
def closure_lr0(items):
    closure = ContainerSet(*items)

    pending = list(items)
    while pending:
        current = pending.pop()
        symbol = current.NextSymbol

        if current.IsReduceItem or symbol.IsTerminal:
            continue

        new_items = [Item(p, 0) for p in symbol.productions if Item(p, 0) not in closure]
        pending += new_items
        closure.extend(new_items)
    return frozenset(closure)


def goto_lr0(items, symbol):
    return frozenset(item.NextItem() for item in items if item.NextSymbol == symbol)


def build_LR0_automaton(G):
    assert len(G.startSymbol.productions) == 1, 'Grammar must be augmented'

    start_production = G.startSymbol.productions[0]
    start_item = Item(start_production, 0)
    start = frozenset([start_item])

    automaton = State(closure_lr0(start), True)

    pending = [start]
    visited = {start: automaton}

    while pending:
        current = pending.pop()
        current_state = visited[current]
        current_closure = current_state.state
        for symbol in G.terminals + G.nonTerminals:
            kernel = goto_lr0(current_closure, symbol)

            if kernel == frozenset():
                continue

            try:
                next_state = visited[kernel]
            except KeyError:
                next_state = visited[kernel] = State(closure_lr0(kernel), True)
                pending.append(kernel)

            current_state.add_transition(symbol.Name, next_state)
    automaton.set_formatter(multiline_formatter)
    return automaton


########################
# LR1 & LALR1 AUTOMATA #
########################
def compress(items):
    centers = {}

    for item in items:
        center = item.Center()
        try:
            lookaheads = centers[center]
        except KeyError:
            centers[center] = lookaheads = set()
        lookaheads.update(item.lookaheads)

    return {Item(x.production, x.pos, set(lookahead)) for x, lookahead in centers.items()}


def expand(item, firsts):
    next_symbol = item.NextSymbol
    if next_symbol is None or not next_symbol.IsNonTerminal:
        return []

    lookaheads = ContainerSet()

    for preview in item.Preview():
        local_first = compute_local_first(firsts, preview)
        lookaheads.update(local_first)

    assert not lookaheads.contains_epsilon

    return [Item(p, 0, lookaheads) for p in next_symbol.productions]


def closure_lr1(items, firsts):
    closure = ContainerSet(*items)
    changed = True
    while changed:
        new_items = ContainerSet()
        for item in closure:
            new_items.extend(expand(item, firsts))
        changed = closure.update(new_items)
    return compress(closure)


def goto_lr1(items, symbol, firsts=None, just_kernel=False):
    assert just_kernel or firsts is not None, '`firsts` must be provided if `just_kernel=False`'
    items = frozenset(item.NextItem() for item in items if item.NextSymbol == symbol)
    return items if just_kernel else closure_lr1(items, firsts)


def build_LR1_automaton(G, firsts=None):
    assert len(G.startSymbol.productions) == 1, 'Grammar must be augmented'

    if not firsts:
        firsts = compute_firsts(G)
    firsts[G.EOF] = ContainerSet(G.EOF)

    start_production = G.startSymbol.productions[0]
    start_item = Item(start_production, 0, lookaheads=(G.EOF,))
    start = frozenset([start_item])

    closure = closure_lr1(start, firsts)
    automaton = State(frozenset(closure), True)

    pending = [start]
    visited = {start: automaton}

    while pending:
        current = pending.pop()
        current_state = visited[current]

        current_closure = current_state.state
        for symbol in G.terminals + G.nonTerminals:
            kernel = goto_lr1(current_closure, symbol, just_kernel=True)

            if kernel == frozenset():
                continue

            try:
                next_state = visited[kernel]
            except KeyError:
                goto = closure_lr1(kernel, firsts)
                visited[kernel] = next_state = State(frozenset(goto), True)
                pending.append(kernel)
            current_state.add_transition(symbol.Name, next_state)

    automaton.set_formatter(multiline_formatter)
    return automaton


def build_LALR1_automaton(G, firsts=None):
    assert len(G.startSymbol.productions) == 1, 'Grammar must be augmented'

    if not firsts:
        firsts = compute_firsts(G)
    firsts[G.EOF] = ContainerSet(G.EOF)

    start_production = G.startSymbol.productions[0]
    start_item = Item(start_production, 0, lookaheads=ContainerSet(G.EOF))
    start = frozenset([start_item.Center()])

    closure = closure_lr1([start_item], firsts)
    automaton = State(frozenset(closure), True)

    pending = [start]
    visited = {start: automaton}

    while pending:
        current = pending.pop()
        current_state = visited[current]

        current_closure = current_state.state
        for symbol in G.terminals + G.nonTerminals:
            goto = goto_lr1(current_closure, symbol, just_kernel=True)
            closure = closure_lr1(goto, firsts)
            center = frozenset(item.Center() for item in goto)

            if center == frozenset():
                continue

            try:
                next_state = visited[center]
                centers = {item.Center(): item for item in next_state.state}
                centers = {item.Center(): (centers[item.Center()], item) for item in closure}

                updated_items = set()
                for c, (itemA, itemB) in centers.items():
                    item = Item(c.production, c.pos, itemA.lookaheads | itemB.lookaheads)
                    updated_items.add(item)

                updated_items = frozenset(updated_items)
                if next_state.state != updated_items:
                    pending.append(center)
                next_state.state = updated_items
            except KeyError:
                visited[center] = next_state = State(frozenset(closure), True)
                pending.append(center)

            if current_state[symbol.Name] is None:
                current_state.add_transition(symbol.Name, next_state)
            else:
                assert current_state.get(symbol.Name) is next_state, 'Bad build!!!'

    automaton.set_formatter(multiline_formatter)
    return automaton
