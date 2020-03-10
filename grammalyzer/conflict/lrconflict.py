from collections import deque

from cmp.automata import State
from cmp.pycompiler import Sentence


def path_from(s):
    """
    Compute path from s to all reacheables states in the automaton from s using a BFS algorithm
    Return a dictionary of parents 'p' where p[some_state] has a tuple where it first item is
    the parent state and the second item is the symbol of the transition from 'parent_state' to
    'some_state', and if a State s is not reacheable from 's' it doesn't belong to the
    returned dictionary. By default the parent of 's' is None.

    The next code can recover the path form s to other reacheable state

    >>> parents = path_from(source)
    >>> path = [dest]
    >>> s = dest
    >>> while parents[s] is not None:
    >>>     s, symbol = parents[s]
    >>>    path += [symbol, s]
    >>> path.reverse()
    >>> return path

    :param s: instance from class State representing the node from where start searching.

    :return: Dict[some_state, Tuple[parent_state, transition_symbol]] where some state is reacheable from state
    """
    queue = deque([s])

    parents = {s: None}
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
    """
    Compute the path in the automaton from state 'source' to state 'dest'.

    :param source: state representing the begining of the path

    :param dest: state representing the end of the path
    
    :return: a list following the secuence
            'source state' -> 'transition symbol' -> 'state' -> ... -> 'transition symbol' -> 'dest state'
    """
    parents = path_from(source)

    path = [dest]
    s = dest
    while parents[s] is not None:
        s, symbol = parents[s]
        path += [symbol, s]
    path.reverse()
    return path


def guided_path(s, guide_sentence):
    """
    Compute a path in the autoamta that follows thre secuence
    's' -> 'guide_sentence[0]' -> 'state' -> ... -> 'guide_sentence[-1]'

    :param s: Begining of the path

    :param guide_sentence: Sentence with the symbols for the transitions from state 's' consuming these symbols

    :return: Path from state 's' consuming the symbols of 'guide'
    """
    path = []
    node = s
    for symbol in guide_sentence:
        path += [node, symbol]
        node = node.get(symbol.Name)
    path.append(node)

    return path


def reduce(s, p, state_list, lookahead):
    """
    Make a backtrack in the automata from state 's' reducing the production 'p'

    :param s: state from reduce

    :param p: production to reduce

    :param state_list: list with all states in the automata

    :param lookahead: the last symbol to append at the path

    :return: a list following the secuence
            's' -> 'transition symbol' -> 'state' -> ... -> 'transition symbol' -> 'dest state' -> 'lookahead'
    """
    states = {s}
    stack = list(p.Right)

    while stack:
        symbol = stack.pop()

        next_states = set()
        for s in state_list:
            if s.has_transition(symbol.Name) and s.get(symbol.Name) in states:
                next_states.add(s)
        states = next_states
    reduced_state = states.pop()

    path = guided_path(reduced_state, p.Right)
    path.append(lookahead)
    return path


def sentence_path(init, conflict_state, symbol, p):
    """
    Computes the path from init automaton state to 'conflict_state' passing
    through state reduced from 'conflict_state' by production 'p'
    """
    states = [s for s in init]
    rpath = reduce(conflict_state, p, states, symbol)
    lpath = path_from_to(init, rpath[0])
    return lpath + rpath[1:]


def expand_path(init, path, follows):
    """
    Expand the non terminal symbols in the given path until all becomes in terminals
    and return a sentence with these sequenced terminals
    """
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
            lookaheads = follows[ritem.Left] if not ritem.lookaheads else ritem.lookaheads

            if lookahead in lookaheads:
                table[current].remove(reductor)
                path = path[:i] + subpath + path[i + 2:]
                break

    return Sentence(*[s for s in path if not isinstance(s, State)])


class LRConflictStringGenerator:
    """
    Recieve a cparser with conflicts and compute a Sentence that show the conflict
    It can be accessed by the field path

    Example:
        >>> g = LRConflictStringGenerator(parser)
        >>> g.path
    """
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
