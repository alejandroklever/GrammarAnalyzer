from collections import deque
from enum import Enum, auto
from typing import List

from cmp.automata import State
from cmp.pycompiler import Production


def path_from(state: State):
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


def path_from_to(source: State, dest: State):
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


def reduce(state: State, production: Production, state_list: List[State], lookahead):
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


def sentence_path(init_state: State, conflict_state: State, production: Production):
    states = [s for s in init_state]
    rpath = reduce(conflict_state, production, states, None)
    lpath = path_from_to(init_state, rpath[0])
    return lpath + rpath[1:]


class ConflictType(Enum):
    ReduceReduce = auto()
    ShiftReduce = auto()


class LRConflictStringGenerator:
    def __init__(self):
        pass
