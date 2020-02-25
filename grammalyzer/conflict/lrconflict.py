from collections import deque

from cmp.automata import State
from cmp.pycompiler import Sentence


def path_from(state):
    queue = deque([state])

    parents = {state: None}
    visited = set()

    while queue:
        current = queue.popleft()

        if current in visited:
            continue

        visited.add(current)

        for symbol in current.transitions:
            dest = current.get(symbol)
            queue.append(dest)
            parents[dest] = current, symbol

    return parents


def path_from_to(source, dest):
    path = [dest]
    parents = path_from(source)

    state = dest
    while parents[state] is not None:
        state, symbol = parents[state]
        path += [symbol, state]
    path.reverse()
    return path


def guided_path(source, guide):
    path = []
    node = source
    for symbol in guide:
        path += [node, symbol]
        node = node.get(symbol.Name)
    path.append(node)

    return path


def reduce(state, production, state_list, lookahead):
    states = {state}
    stack = list(production.Right)

    while stack:
        symbol = stack.pop()

        next_states = set()
        for s in state_list:
            if s.has_transition(symbol.Name) and s.get(symbol.Name) in states:
                next_states.add(s)
        states = next_states
    reduced_state = states.pop()

    path = guided_path(reduced_state, production.Right)
    path.append(lookahead)
    return path


def sentence_path(init, conflict_state, symbol, production):
    states = [s for s in init]
    rpath = reduce(conflict_state, production, states, symbol)
    lpath = path_from_to(init, rpath[0])
    return lpath + rpath[1:]


def expand_path(init, path, follows):
    i = -2
    table = {s: set(s.state) for s in init}

    lookahead = path[-1]
    while i >= -len(path):
        current = path[i]
        symbol = path[i + 1]

        if symbol.IsTerminal:
            lookahead = symbol
            i -= 2
            continue

        reductors = [item for item in current.state if item.production.Left == current and item in table[current]]

        while reductors:
            reductor = reductors.pop()

            subpath = guided_path(current, reductor.production.Right)

            last = subpath.pop()
            ritem = [item for item in last.state if item.IsReduceItem and item.production == reductor.production][0]
            if not ritem.lookaheads:
                lookaheads = follows[ritem.Left]
            else:
                lookaheads = ritem.lookaheads

            if lookahead in lookaheads:
                table[current].remove(reductor)
                path = path[:i] + subpath + path[i + 2:]
                break

    return Sentence(*[s for s in path if not isinstance(s, State)])


class LRConflictStringGenerator:
    def __init__(self, parser):
        assert parser.conflict is not None, 'Expected parser with conflict...'
        stateID = parser.state_dict
        state = parser.conflict.state
        symbol = parser.conflict.symbol
        init = parser.automaton
        _, production = parser.action[state, symbol].pop()
        path = sentence_path(init, stateID[state], symbol, production)

        self.production = production
        self.conflict = parser.conflict
        self.path = expand_path(init, path, parser.follows)
