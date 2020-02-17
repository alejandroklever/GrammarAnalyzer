from cmp.pycompiler import Grammar
from .automata import NFA, DFA

EPSILON = 'ε'


def check_for_regular_grammar(G: Grammar):
    productions = G.Productions
    start_symbol = G.startSymbol

    # Check for condition A -> a B
    # where A, B are non terminals and a is a terminal
    for prod in productions:
        head, body = prod
        if len(body) == 2:
            if not (body[0].IsTerminal and body[1].IsNonTerminal):
                return False
        elif len(body) == 1:
            if not body[0].IsTerminal:
                return False
        elif len(body) == 0:
            if not (body.IsEpsilon and head == start_symbol):
                return False
        else:
            return False
    return True


def build_automata_from_rg(G: Grammar):
    for i, nonterminal in enumerate(G.nonTerminals):
        nonterminal.id = i

    nonTerminals = G.nonTerminals
    start = G.startSymbol.id
    final = len(nonTerminals)

    transitions = {}

    for head, body in G.Productions:
        if len(body) == 2:
            symbol, next_state = body
            try:
                transitions[head.id, symbol.Name].append(next_state.id)
            except KeyError:
                transitions[head.id, symbol.Name] = [next_state.id]
        elif len(body) == 1:
            symbol = body[0]
            try:
                transitions[head.id, symbol.Name].append(final)
            except KeyError:
                transitions[head.id, symbol.Name] = [final]
        else:
            try:
                transitions[head.id, ''].append(final)
            except KeyError:
                transitions[head.id, ''] = [final]

    return NFA(len(nonTerminals) + 1, finals=[final], transitions=transitions, start=start)


def dfa_to_regex(dfa: DFA):
    start = dfa.states
    final = dfa.states + 1
    transitions = {}
    middle_states = list(range(dfa.states))

    # Compactar arcos multiples
    for x in dfa.transitions:
        # Dado el estado x por cada estado destino d se unen
        # los simbolos que provocan una transicion de x -> d
        compacted_arcs = {}
        for regex in dfa.transitions[x]:
            d = dfa.transitions[x][regex][0]
            try:
                compacted_arcs[d].append(regex)
            except KeyError:
                compacted_arcs[d] = [regex]

        # Compactar los arcos multiples
        # etiquetandolos con la union de los simbolos
        for d, symbols in compacted_arcs.items():
            transitions[x, d] = '|'.join(symbols) if x != d else f'({"|".join(symbols)})*'

    for f in dfa.finals:
        transitions[f, final] = EPSILON
    transitions[start, dfa.start] = EPSILON

    # Por cada estado intermedio...
    while middle_states:

        x = middle_states.pop()  # Estado para eliminacion

        # Computar indegree y outdegree del estado x
        # con los arcos compactados para tener un acceso
        # mas rapido en cada estado intermedio
        in_deg = [(s, regex) for (s, d), regex in transitions.items() if d == x and s != d]
        out_deg = [(d, regex) for (s, d), regex in transitions.items() if s == x and d != s]

        # Checkeamos que si el estado x tiene auto-transiciones
        try:
            mid_regex = transitions[x, x]
            del transitions[x, x]
        except KeyError:
            mid_regex = ''

        # Creamos las nuevas aristas eliminando al estado x del automata
        for l, left_regex in in_deg:
            for r, right_regex in out_deg:
                left_regex = '' if left_regex == EPSILON else f'({left_regex})'
                right_regex = '' if right_regex == EPSILON else f'({right_regex})'
                mid_regex = '' if not mid_regex else f'({mid_regex})'

                regex = left_regex + mid_regex + right_regex

                try:  # Comprobamos si ya existe una transicion entre l y r para compactar la arista
                    previous_regex = transitions[l, r]  # Buscamos la regex de la arista anterior
                    regex = f'{previous_regex}|{regex}'  # Unimos las expresiones regulares de las transiciones
                except KeyError:
                    pass

                transitions[l, r] = regex if r != l else f'({regex})*'  # Insertamos en la tablas de transiciones

        # Eliminamos transiciones que entran y salen del estado x
        for l, _ in in_deg:
            del transitions[l, x]

        for r, _ in out_deg:
            del transitions[x, r]

    assert (start, final) in transitions, 'State Elimination Error...'

    regex = transitions[start, final]

    change = True
    while change:
        new_regex = clean_regex(regex)
        change = new_regex != regex
        regex = new_regex

    return clean_regex(regex)


def clean_regex(regex):
    stack = []
    invalid = [False] * len(regex)
    for i, c in enumerate(regex):
        if c == '(':
            stack.append(i)
        if c == ')':
            j = stack.pop()
            invalid[i] = invalid[j] = (i - j in [1, 2]) or (i - j == 3 and regex[i - 1] == '*')

    s = ''
    for i, c in enumerate(regex):
        if not invalid[i]:
            s += c
    return s
