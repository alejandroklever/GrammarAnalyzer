from cmp.utils import ContainerSet


def compute_local_first(firsts, alpha):
    first_alpha = ContainerSet()

    try:
        alpha_is_epsilon = alpha.IsEpsilon
    except AttributeError:
        alpha_is_epsilon = False

    if alpha_is_epsilon:
        first_alpha.set_epsilon()
    else:
        for symbol in alpha:
            first_symbol = firsts[symbol]
            first_alpha.update(first_symbol)
            if not first_symbol.contains_epsilon:
                break
        else:
            first_alpha.set_epsilon()

    return first_alpha


def compute_firsts(G):
    firsts = {}
    change = True

    for terminal in G.terminals:
        firsts[terminal] = ContainerSet(terminal)

    for nonterminal in G.nonTerminals:
        firsts[nonterminal] = ContainerSet()

    while change:
        change = False

        # P: X -> alpha
        for production in G.Productions:
            X, alpha = production

            first_X = firsts[X]

            try:
                first_alpha = firsts[alpha]
            except KeyError:
                first_alpha = firsts[alpha] = ContainerSet()

            local_first = compute_local_first(firsts, alpha)

            change |= first_alpha.hard_update(local_first)
            change |= first_X.hard_update(local_first)

    return firsts


def compute_follows(G, firsts):
    follows = {}
    change = True

    local_firsts = {}

    # init Follow(Vn)
    for nonterminal in G.nonTerminals:
        follows[nonterminal] = ContainerSet()
    follows[G.startSymbol] = ContainerSet(G.EOF)

    while change:
        change = False

        # P: X -> alpha
        for production in G.Productions:
            X = production.Left
            alpha = production.Right

            follow_X = follows[X]

            for i, symbol_Y in enumerate(alpha):
                # X -> zeta Y beta
                if symbol_Y.IsNonTerminal:
                    follow_Y = follows[symbol_Y]
                    try:
                        first_beta = local_firsts[alpha, i]
                    except KeyError:
                        first_beta = local_firsts[alpha, i] = compute_local_first(firsts, alpha[i + 1:])
                    # First(beta) - { epsilon } subset of Follow(Y)
                    change |= follow_Y.update(first_beta)
                    # beta ->* epsilon or X -> zeta Y ? Follow(X) subset of Follow(Y)
                    if first_beta.contains_epsilon:
                        change |= follow_Y.update(follow_X)
    # Follow(Vn)
    return follows


# def find_shortest_production_path(G: Grammar, x: NonTerminal) -> List[Production]:
#     queue = deque([G.startSymbol])
#     parent = {G.startSymbol: None}
#     transition = {G.startSymbol: None}
#     break_all = False
#     current = None
#
#     while queue:
#         current = queue.popleft()
#         for prod in current.productions:
#             for symbol in prod.Right:
#                 try:
#                     parent[symbol]
#                 except KeyError:
#                     parent[symbol] = current
#                     transition[symbol] = prod
#                     if symbol in G.nonTerminals:
#                         queue.append(symbol)
#                     if symbol == x:
#                         break_all = True
#                         current = symbol
#                         break
#             if break_all:
#                 break
#         if break_all:
#             break
#     list_prod = []
#     while parent[current] is not None:
#         list_prod.append(transition[current])
#         current = parent[current]
#     list_prod.reverse()
#     return list_prod
#
#
# def concat_production(productions: List[Production]) -> List[Symbol]:
#     return _concat_production(productions, 0, [])
#
#
# def _concat_production(productions: List[Production], i: int, sentence: List[Symbol]) -> List[Symbol]:
#     current_prod = productions[i]
#     for symbol in current_prod.Right:
#         if i < (len(productions) - 1):
#             if symbol != productions[i + 1].Left:
#                 sentence.append(symbol)
#             else:
#                 _concat_production(productions, i + 1, sentence)
#         else:
#             sentence.append(symbol)
#     return sentence
