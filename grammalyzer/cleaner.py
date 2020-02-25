from cmp.pycompiler import Grammar, Sentence


def delete_common_prefix(G: Grammar):
    """
    Algoritmo para eliminar los prefijos comunes de las producciones con la misma cabecera
    Por cada no terminal busca si dos de sus produciones tiene prefijos comunes
    """
    for nonterminal in G.nonTerminals:
        change = True
        primes = ''
        while change:
            change = False
            for production0 in nonterminal.productions:
                _continue = False
                for production1 in nonterminal.productions:
                    if production0 != production1:
                        lpc = 0
                        for i in range((min(len(production0.Right), len(production1.Right)))):
                            if production0.Right[i] == production1.Right[i]:
                                lpc += 1
                            else:
                                break
                        # En caso de que si tengan prefijos comunes se realiza el siguiente cambio:
                        # E -> aA | aB
                        # Entonces se cambia por :
                        # E -> aE'
                        # E' -> A | B
                        if lpc > 0:
                            primes += '\''
                            temp = G.NonTerminal(f"{nonterminal.Name}{primes}", False)
                            nonterminal.productions.remove(production0)
                            nonterminal.productions.remove(production1)
                            G.Productions.remove(production0)
                            G.Productions.remove(production1)
                            nonterminal %= Sentence(*production0.Right[0:lpc] + (temp,))
                            alpha = production0.Right[lpc:]
                            betha = production1.Right[lpc:]
                            if len(alpha) == 0:
                                temp %= G.Epsilon
                            else:
                                temp %= Sentence(*alpha)
                            if len(betha) == 0:
                                temp %= G.Epsilon
                            else:
                                temp %= Sentence(*betha)
                            change = True
                            _continue = True
                            break
                if _continue:
                    continue
    return G


def delete_inmidiate_left_recursion(G: Grammar):
    # Algoritmo para eliminar la recursion izquierda inmediata
    # Seria conveniente adaptarlo para que funciona sin crar una gramatica nueva pero en un principio es funcional
    Gnew = Grammar()
    Gnew.terminals = G.terminals

    for nonterminal in G.nonTerminals:
        for production in nonterminal.productions:
            if len(production.Right) > 0 and production.Right[0] == nonterminal:
                # para cada no terminal con recursion izquierda inmediata creamos un nuevo terminal
                # A -> Ab | c
                # c y b formas oracionales sin A en el principio
                A = Gnew.NonTerminal(nonterminal.Name, nonterminal == G.startSymbol)
                B = Gnew.NonTerminal(f"{nonterminal.Name}'", False)
                # B == A`
                # Las producciones de A son separadas en produciones de A y B de manera equivalente de la siguiente manera
                for prod in nonterminal.productions:
                    if len(prod.Right) > 0 and prod.Right[0] == nonterminal:
                        # Las que tengan recursion izquierda
                        B %= Sentence(*(prod.Right[1:] + (B,)))
                        # A` -> bA`
                    else:
                        A %= prod.Right + B
                        # A -> cA`
                B %= Gnew.Epsilon
                # A1 -> bA` | epsilon
                break
        else:
            # si no tiene recursion izquierda inmediata mantengo el no terminal
            A = Gnew.NonTerminal(nonterminal.Name)
            for production in nonterminal.productions:
                A %= production.Right
    return Gnew


####################
#  GrammarCleaner  #
####################
def clean_grammar(G: Grammar):
    # El metodo de limpiar la gramatica Esta compuesto por varios pasos, sus nombres son suficientemente descriptivos

    G = delete_epsilon(G)
    G = delete_unary_productions(G)
    G = delete_nonterminal_variables(G)
    G = delete_unreacheable_variables(G)
    return G


def delete_epsilon(G: Grammar):
    # para eliminar las epsilon produciones encontramos el conjunto de los elementos nuleables
    # estos elementos son aquellos que tras una o mas produccions se vuelvan epsilon
    # A ->* epsilon => A es nulleable
    nullable = set()
    change = True
    while change:
        n = len(nullable)
        for head, body in G.Productions:

            if head in nullable:
                continue

            if len(body) == 0:
                nullable.add(head)
            else:
                if all(symbol in nullable for symbol in body):
                    nullable.add(head)
        change = n != len(nullable)

    # Dado que tenemos los elementos nulleables para todas las produciones
    # si una produccion tiene un elemento nulleable esta es sustituida:
    # por esta misma produccion y la produccion sin el elemento nulleabe
    # Las epsilon producciones son eliminadas
    for nonterminal in G.nonTerminals:
        queue = [x for x in nonterminal.productions]
        dic = {}
        while queue:
            production = queue.pop()
            if len(production.Right) == 0:
                G.Productions.remove(production)
                nonterminal.productions.remove(production)
            else:
                for i, symbol in enumerate(production.Right):
                    if symbol in nullable:
                        add_production(nonterminal,
                                       Sentence(*(production.Right[:max(i, 0)] + production.Right[i + 1:])),
                                       dic, queue, True)
    return G


def delete_unary_productions(G: Grammar):
    ## para eliminar cada producion unitaria de la forma:
    ## A -> B
    ## B -> C | D | EF
    ## Simplemete "Subimos las produciones unitarias"
    ## es decir la adelantamos pues no es necesario producir B para que esta produzca e resto o se:
    ## A -> C | D | EF
    ## B -> C | D | EF

    change = True
    while change:
        change = False
        for production in G.Productions:
            head, body = production
            if len(body) == 1 and body[0] in G.nonTerminals:
                G.Productions.remove(production)
                head.productions.remove(production)
                for _, right in body[0].productions:
                    head %= right
                change = True
    return G


def delete_nonterminal_variables(G: Grammar):
    # Todas aquellos no terminales que no deriven en algun string terminal tras 1 o mas producciones
    # No son necesarias pues las cadenas siempre estaran formadas unicaente por terminales
    # y produciones que no generen terminales son inconsistentes con esta verdad
    # por tanto no aportan informacion al lenguaje
    # Y no son necesarias en la gramatica

    # Computamos el conjunto de las produciones que derivan en terminales tra una o mas produciones
    # La demostracion de la correctitud de este algoritmo puede ser inductiva
    # buscamos las cadenas que terminen en terminales tras una produccion luego tras dos y asi sucesivamente
    derive_to_terminal = set()
    change = True
    while change:
        n = len(derive_to_terminal)
        for nonterminal in G.nonTerminals:
            for _, body in nonterminal.productions:
                if all(symbol in derive_to_terminal for symbol in body if symbol.IsNonTerminal):
                    derive_to_terminal.add(nonterminal)
        change = n != len(derive_to_terminal)

    # Las produciones posean uno de los terminales que no derivan en string terminales son incosistentes
    # Pues estas no terminarian en un string terminal
    # Ya sea si lo poseen en la cabecera como en el cuerpo  de la produccion
    # estas producciones inconsistentes son guardadas en Removable
    removable = set()
    for prod in G.Productions:
        head, body = prod
        if head in derive_to_terminal:
            if any(symbol not in derive_to_terminal for symbol in body if symbol.IsNonTerminal):
                removable.add(prod)
        else:
            removable.add(prod)

    # Son removidas de la gramatica las producciones y no terminales inconsistentes
    for production in removable:
        G.Productions.remove(production)
        production.Left.productions.remove(production)

    for nonterminal in G.nonTerminals:
        if not nonterminal.productions:
            G.nonTerminals.remove(nonterminal)

    return G


def delete_unreacheable_variables(G: Grammar):
    # Para eliminar mas rapido castearemos las listas a set,
    # de esta forma la eliminacion sera O(1)
    G.terminals = set(G.terminals)
    G.nonTerminals = set(G.nonTerminals)
    G.Productions = set(G.Productions)

    # Los elementos que no pueden ser alcanzados por una o mas producciones del caracter inicial
    # No son necesarias pues nunca son utilizadas para generar ningun elemento del lenguaje
    # estos elementos inalcanzables pueden ser tanto terminales como no terminales
    stack = [G.startSymbol]
    reacheable_nonterminals = {G.startSymbol}
    reacheable_terminals = set()

    # Encontramos los terminales y no terminales alcanzables
    while stack:
        current = stack.pop()
        for _, body in current.productions:
            for symbol in body:
                if symbol.IsNonTerminal:
                    if symbol not in reacheable_nonterminals:
                        reacheable_nonterminals.add(symbol)
                        stack.append(symbol)
                else:
                    reacheable_terminals.add(symbol)

    # Eliminamos las producciones con elementos no alcanzables
    G.Productions -= {production for production in G.Productions if production.Left not in reacheable_nonterminals}

    # Ahora removemos los no terminales no alcanzables
    G.nonTerminals -= {nonterminal for nonterminal in G.nonTerminals if nonterminal not in reacheable_nonterminals}

    # Ahora removemos los terminales no alcanzables
    G.terminals -= {terminal for terminal in G.terminals if terminal not in reacheable_terminals}

    # Finalmente casteamos a lista otra vez
    G.terminals = list(G.terminals)
    G.nonTerminals = list(G.nonTerminals)
    G.Productions = list(G.Productions)
    return G


def add_production(nonterminal, sentence, dic, queue, enqueue):
    """
    Metodo auxiliar para agregar nuevas produciones a la gramatica
    Tambien actualiza la cola si enqueue = true y el diccionario de elementos usados
    """
    try:
        dic[sentence]
    except KeyError:
        dic[sentence] = True
        if len(sentence) > 0:
            nonterminal %= sentence
        if enqueue:
            queue.append(nonterminal.productions[-1])


if __name__ == '__main__':
    G = Grammar()
    E = G.NonTerminal('E', True)
    T, F = G.NonTerminals('T F')
    plus, minus, star, div, opar, cpar, num = G.Terminals('+ - * / ( ) int')

    E %= E + plus + E | E + star + E | T
    T %= num + opar + E + cpar | num | num + star + num | num + star + num + star
    print("Probando eliminacion de prefijos comunes")
    print(delete_common_prefix(G))

    G = Grammar()
    E = G.NonTerminal('E', True)
    T, F = G.NonTerminals('T F')
    plus, minus, star, div, opar, cpar, num = G.Terminals('+ - * / ( ) int')

    E %= E + plus + T | T  # | E + minus + T
    T %= T + star + F | F  # | T + div + F
    F %= num | opar + E + cpar
    print("\n\nProbando recursion izquierda inmediata")
    print(delete_inmidiate_left_recursion(G))

    G = Grammar()
    S = G.NonTerminal('S', True)
    A, B, C, D, F = G.NonTerminals('A B C D F')
    a, b, d, f = G.Terminals('a b d f')

    S %= A + B + C
    A %= a + A | G.Epsilon
    B %= b + B | G.Epsilon
    C %= G.Epsilon
    D %= d + D | f
    F %= f

    print("\n\nCleaned Gramar")
    print(clean_grammar(G))
