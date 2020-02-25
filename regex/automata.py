import pydot
from cmp.utils import ContainerSet, DisjointSet


class NFA:
    def __init__(self, states, finals, transitions, start=0):
        self.states = states
        self.start = start
        self.finals = set(finals)
        self.map = transitions
        self.vocabulary = set()
        self.transitions = {state: {} for state in range(states)}

        for (origin, symbol), destinations in transitions.items():
            assert hasattr(destinations, '__iter__'), 'Invalid collection of states'
            self.transitions[origin][symbol] = destinations
            self.vocabulary.add(symbol)

        self.vocabulary.discard('')

    def epsilon_transitions(self, state):
        assert state in self.transitions, 'Invalid state'
        try:
            return self.transitions[state]['']
        except KeyError:
            return ()

    def graph(self):
        G = pydot.Dot(graph_type='digraph', rankdir='LR', margin=0.1)
        G.add_node(pydot.Node('start', shape='plaintext', label='', width=0, height=0))

        for (start, tran), destinations in self.map.items():
            tran = 'ε' if tran == '' else tran
            G.add_node(pydot.Node(start, shape='circle', style='bold' if start in self.finals else ''))
            for end in destinations:
                G.add_node(pydot.Node(end, shape='circle', style='bold' if end in self.finals else ''))
                G.add_edge(pydot.Edge(start, end, label=tran, labeldistance=2))

        G.add_edge(pydot.Edge('start', self.start, label='', style='dashed'))
        return G

    def _repr_svg_(self):
        try:
            return self.graph().create_svg().decode('utf8')
        except:
            pass


class DFA(NFA):

    def __init__(self, states, finals, transitions, start=0):
        assert all(isinstance(value, int) for value in transitions.values())
        assert all(len(symbol) > 0 for origin, symbol in transitions)

        transitions = {key: [value] for key, value in transitions.items()}
        NFA.__init__(self, states, finals, transitions, start)
        self.current = start

    def _move(self, symbol):
        try:
            self.current = self.transitions[self.current][symbol][0]
            return True
        except KeyError:
            return False

    def _reset(self):
        self.current = self.start

    def recognize(self, string):
        self._reset()
        for char in string:
            if not self._move(char):
                return False
        return self.current in self.finals

    @staticmethod
    def from_nfa(automaton):
        return nfa_to_dfa(automaton)

    @staticmethod
    def minimize(automaton):
        return automata_minimization(automaton)


#########################
# NFA -> DFA Convertion #
#########################
def move(automaton, states, symbol):
    moves = set()
    for state in states:
        symbols = automaton.transitions[state]
        try:
            moves.update({s for s in symbols[symbol]})
        except KeyError:
            continue
    return moves


def epsilon_closure(automaton, states):
    pending = list(states)
    closure = set(states)

    while pending:
        state = pending.pop()
        symbols = automaton.epsilon_transitions(state)

        for s in symbols:
            if s not in closure:
                pending.append(s)
                closure.add(s)

    return ContainerSet(*closure)


def nfa_to_dfa(automaton):
    transitions = {}

    start = epsilon_closure(automaton, [automaton.start])
    start.id = 0
    start.is_final = any(s in automaton.finals for s in start)
    states = [start]

    pending = [start]
    while pending:
        state = pending.pop()

        for symbol in automaton.vocabulary:
            state_move = move(automaton, state, symbol)
            e_clousure = epsilon_closure(automaton, state_move)

            if e_clousure == set():
                continue

            if e_clousure not in states:
                e_clousure.id = states[-1].id + 1
                e_clousure.is_final = any(s in automaton.finals for s in e_clousure)

                states.append(e_clousure)
                pending.append(e_clousure)
            else:
                e_clousure = next(s for s in states if s == e_clousure)

            try:
                transitions[state.id, symbol]
                assert False, 'Invalid DFA!!!'
            except KeyError:
                transitions[state.id, symbol] = e_clousure.id

    finals = [state.id for state in states if state.is_final]
    dfa = DFA(len(states), finals, transitions)
    return dfa


#######################
# Automata operations #
#######################
def automata_union(a1, a2):
    transitions = {}

    start = 0
    d1 = 1
    d2 = a1.states + d1
    final = a2.states + d2

    for (origin, symbol), destinations in a1.map.items():
        transitions[origin + d1, symbol] = [d + d1 for d in destinations]

    for (origin, symbol), destinations in a2.map.items():
        transitions[origin + d2, symbol] = [d + d2 for d in destinations]

    transitions[start, ''] = [a1.start + d1, a2.start + d2]
    finals = [f + d1 for f in a1.finals] + [f + d2 for f in a2.finals]
    for f in finals:
        transitions[f, ''] = [final]

    states = a1.states + a2.states + 2
    finals = {final}

    return NFA(states, finals, transitions, start)


def automata_concatenation(a1, a2):
    transitions = {}

    start = 0
    d1 = 0
    d2 = a1.states + d1
    final = a2.states + d2

    for (origin, symbol), destinations in a1.map.items():
        transitions[origin + d1, symbol] = [d + d1 for d in destinations]

    for (origin, symbol), destinations in a2.map.items():
        transitions[origin + d2, symbol] = [d + d2 for d in destinations]

    for f in a1.finals:
        transitions[f + d1, ''] = [a2.start + d2]

    for f in a2.finals:
        transitions[f + d2, ''] = [final]

    states = a1.states + a2.states + 1
    finals = {final}

    return NFA(states, finals, transitions, start)


def automata_closure(a1):
    transitions = {}

    start = 0
    d1 = 1
    final = a1.states + d1

    for (origin, symbol), destinations in a1.map.items():
        transitions[origin + d1, symbol] = [d + d1 for d in destinations]
    transitions[start, ''] = [a1.start + d1, final]

    for f in a1.finals:
        try:
            X = transitions[f + d1, '']
        except KeyError:
            X = transitions[f + d1, ''] = set()
        X.add(final)
        X.add(a1.start + d1)

    states = a1.states + 2
    finals = {final}

    return NFA(states, finals, transitions, start)


######################
# Minimize Automaton #
######################
def distinguish_states(group, automaton, partition):
    split = {}
    vocabulary = tuple(automaton.vocabulary)
    for member in group:
        transitions = automaton.transitions[member.value]
        destinations = ((transitions[s][0] if s in transitions else None) for s in vocabulary)
        representative = tuple((partition[d].representative if d is not None else None) for d in destinations)
        try:
            split[representative].append(member.value)
        except KeyError:
            split[representative] = [member.value]

    return [group for group in split.values()]


def state_minimization(automaton):
    partition = DisjointSet(*range(automaton.states))

    ## partition = { NON-FINALS | FINALS }
    partition.merge(automaton.finals)
    partition.merge([x for x in range(automaton.states) if x not in automaton.finals])

    while True:
        new_partition = DisjointSet(*range(automaton.states))

        for group in partition.groups:
            for subgroup in distinguish_states(group, automaton, partition):
                new_partition.merge(subgroup)

        if len(new_partition) == len(partition):
            break

        partition = new_partition

    return partition


def automata_minimization(automaton):
    partition = state_minimization(automaton)

    states = [s for s in partition.representatives]

    transitions = {}

    index = {state: i for i, state in enumerate(states)}

    for i, state in enumerate(states):
        origin = state.value

        for symbol, destinations in automaton.transitions[origin].items():
            r = partition[destinations[0]].representative

            try:
                transitions[i, symbol]
                assert False
            except KeyError:
                transitions[i, symbol] = index[r]

    finals = list({index[partition[f].representative] for f in automaton.finals})
    start = index[partition[automaton.start].representative]

    return DFA(len(states), finals, transitions, start)
